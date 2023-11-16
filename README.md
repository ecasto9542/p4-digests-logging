# p4-digests
Barebones repo for getting started sending and receiving digest messages on a p4 bmv2 switch. Please run this in the VM provided by P4 in this p4 repo: https://github.com/p4lang/tutorials

General Steps:
- Navigate to an item in the src folder (boilerplate, pmu_example, e.t.c)
- Call `make run`
- xterm into h1, s1, and h2

General Notes:
- To adjust the topology of the network adjust the `topology.json` folder in each example's `pod-topo` folder

To try the pmu_example:
- Call `make run`
- In mininet, call `xterm h1 h2 s1`
- Navigate to s1's terminal
- Run `simple_switch_CLI < rules.cmd` to install the forwarding rules on the device
- Run `python3 controller.py` to enable a script that listens for digest messages
- Navigate to `h2`'s terminal
- Run `python3 receive.py --terminate_after <the  number of packets you expect to receive>`
- Navigate to `h1`'s terminal
- Run `python3 send.py pmu12.csv`
