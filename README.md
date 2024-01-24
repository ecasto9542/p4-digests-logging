# p4-digests
Barebones repo for getting started sending and receiving digest messages on a p4 bmv2 switch. Please run this in the VM provided by P4 in this p4 repo: https://github.com/p4lang/tutorials

General Steps:
- Navigate to an item in the src folder (boilerplate, pmu_example, e.t.c)
- Call `make run`
- Dont forget to load table rules using simple_switch_CLI < rules.cmd
- xterm into h1, s1, and h2

General Notes:
- To adjust the topology of the network adjust the `topology.json` folder in each example's `pod-topo` folder

To try the pmu_example:
- Navigate to the pmu_example folder
- Call `make run`
- In mininet, call `xterm h1 h2 s1`
- Navigate to s1's terminal
- Run `simple_switch_CLI < rules.cmd` to install the forwarding rules on the device
- Run `python3 controller.py --terminate_after 100` to enable a script that listens for digest messages. The 100 is arbitrary in this case (the program will end after generating 100 packets)
- Navigate to `h2`'s terminal
- Run `python3 receive.py --terminate_after <the  number of packets you expect to receive>`
- Navigate to `h1`'s terminal
- Run `python3 send.py pmu12.csv --num_packets 100`
- Notice that `h2`s terminal has recieved all packets
- Go into pmu_example/missing-data.json and add in a set of indexes between 1-100
- Re-run the receive.py script
- Re-run the send.py script
- Notice that s1 generate packets to send to h2
- Effectively, if you have 5 missing indexes in your missing indexes file, you only send 95 packets from send.py. Receive.py receives 100 packets, meaning the switch made up the difference

Testing eva committing
