/*************************************************************************
This is a simple P4 program that forwards packets through a network and
enables a developer to easily send a digest message to the control plane


*************************************************************************/


/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<8> TYPE_UDP = 0x11;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header udp_t{
  bit<16> srcPort;
  bit<16> desPort;
  bit<16> len;
  bit<16> checksum;
}

header pmu_t {
    bit<16>   sync;
    bit<16>   frame_size;
    bit<16>   id_code;
    bit<32>   soc;
    bit<32>   fracsec;
    bit<16>   stat;
    bit<64>   phasors;
    bit<16>   freq;
    bit<16>   dfreq;
    bit<32>   analog;
    bit<16>   digital;
    bit<16>   chk;
}

struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    udp_t          udp;
    pmu_t          pmu;
}


//add in the information for a packet that you want to log
struct digest_pmu_packet {
  bit<32>   soc0;
  bit<32>   fracsec0;
  bit<64>   phasors0;
  bit<32>   curr_soc;
  bit<32>   curr_fracsec;
}

struct metadata {
    digest_pmu_packet digest_packet;
}


/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol){
            TYPE_UDP: parse_udp;
            default: accept;
        }
    }


    //swap out UDP parser for TCP parser
    state parse_udp {
        packet.extract(hdr.udp);
        transition select(hdr.udp.desPort){
            4712: parse_pmu;
            default: accept;
        }
    }

    state parse_pmu {
        packet.extract(hdr.pmu);
        transition accept;
    }

}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/
struct phasor_t {
  bit<32> magnitude;
  bit<32> angle;
}
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    register<bit<32>>(1) prev_fracsec_regs;
    register<bit<32>>(1) prev_soc_regs;

    register<bit<32>>(1) frac_sec_regs;
    register<bit<32>>(1) soc_regs;
    register<bit<32>>(1) magnitude_regs;
    register<bit<32>>(1) phase_angle_regs;
    register<bit<32>>(1) R1;

    bit<32> new_reg2;
    bit<32> digest_counter;

    bit<32> temp_mag;
    bit<32> temp_ang;


    action drop() {
        mark_to_drop(standard_metadata);
    }

    action send_digest_message() {
        //set meta.digest_packet equal to the information that you want to send to the control plane
        //meta.digest_packet.some_number = (bit<32>)1234;

        // 0 is top of stack and most recent packets

        magnitude_regs.read(temp_mag, (bit<32>)0);
        phase_angle_regs.read(temp_ang, (bit<32>)0);
        meta.digest_packet.phasors0 = temp_mag ++ temp_ang;
        soc_regs.read(meta.digest_packet.soc0, (bit<32>)0);
        frac_sec_regs.read(meta.digest_packet.fracsec0, (bit<32>)0);

        R1.write((bit<32>)0, meta.digest_packet.fracsec0);

        meta.digest_packet.curr_soc = hdr.pmu.soc;
        meta.digest_packet.curr_fracsec = hdr.pmu.fracsec;

        digest(1, meta.digest_packet);
    }

    action update_registers() {
        //0 is top of stack
        //TODO: remove frac_sec_regs if you don't need them. Double check though
        frac_sec_regs.read(new_reg2, (bit<32>)0);
        frac_sec_regs.write((bit<32>)0, hdr.pmu.fracsec);

        soc_regs.read(new_reg2, (bit<32>)0);
        soc_regs.write((bit<32>)0, hdr.pmu.soc);

        magnitude_regs.read(new_reg2, (bit<32>)0);
        magnitude_regs.write((bit<32>)0, (bit<32>)(hdr.pmu.phasors >> 32));

        phase_angle_regs.read(new_reg2, (bit<32>)0);
        phase_angle_regs.write((bit<32>)0, (bit<32>)hdr.pmu.phasors);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    apply {

        if (hdr.ipv4.isValid()) {
            bit <32> prev_fracsec;
            bit <32> prev_soc;
            //conditionally send data to the control plane here using the send_digest_message action
            if(hdr.pmu.stat == (bit<16>)0x0)
            {
              soc_regs.read(prev_soc, (bit<32>)0);
              frac_sec_regs.read(prev_fracsec, (bit<32>)0);
            
            //check if diff_soc is non_zero:
            // if it is non_zero (greater than a second delay), send a digest
            // if it is zero, check the diff_frac_sec
            // TODO: fix this algo since we could have 13.9xxx and 14.01xxx
            bit<32> diff_soc = (hdr.pmu.soc - prev_soc);

            if(diff_soc!=0 && prev_soc != 0){
                send_digest_message();
            }
            else{
                bit<32>frac_sec_diff = hdr.pmu.fracsec - prev_fracsec;
                if(frac_sec_diff > 20000 && prev_soc != 0) 
                {
                    send_digest_message();
                }
            }
            update_registers();
            //if not delayed
            prev_fracsec_regs.write((bit<32>)0, hdr.pmu.fracsec);
            prev_soc_regs.write((bit<32>)0, hdr.pmu.soc);
            // if (hdr.pmu.soc < prev_soc)
            // {
            //     //log the packet
            //     send_digest_message();
            // }
            // else if (hdr.pmu.fracsec < prev_fracsec)
            // {
            //     //log packet
            //     send_digest_message();
            // }
            // //forward packet
            // prev_fracsec_regs.write((bit<32>)0, hdr.pmu.fracsec);
            // prev_soc_regs.write((bit<32>)0, hdr.pmu.soc);

            // //difference between packet arrival times in microseconds
            // bit<32> frac_sec_diff = soc_diff_in_frac_sec - temp_frac_sec + hdr.pmu.fracsec;
            
            }


            ipv4_lpm.apply();
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {

    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
        update_checksum(
        hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {

    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.pmu);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
