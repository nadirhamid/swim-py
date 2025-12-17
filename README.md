# PySWIM: Scalable Membership and Failure Detection

**PySWIM** is a lightweight Python implementation of the **SWIM** (Scalable Weakly-consistent Infection-style Process Group Membership) protocol. It provides an efficient way for nodes in a distributed system to maintain a list of healthy peers without the overhead of traditional heartbeat mechanisms.

### Why SWIM?

Traditional heartbeat protocols scale poorly (O(n^2) messages). SWIM solves this by using a gossip-based strategy that provides:

* **Constant network load** per node.
* **Low false-positive** failure detection using a "Suspect" mechanism.
* **Scalable group membership** updates via infection-style dissemination.

---

## 🚀 Use Cases

* **Prototyping:** Quickly test SWIM’s failure detection latency and accuracy in your specific network environment.
* **Learning:** A clean, readable implementation for those studying distributed algorithms.
* **Lightweight Coordination:** Manage group membership for small-to-medium clusters where full-blown solutions like Consul or ZooKeeper are overkill.

## 🛠 Installation

Currently, this module supports **Python 2.7**. You can install it directly from the source:

```bash
git clone https://github.com/nadirhamid/swim-python.git
cd swim-python
python setup.py install

```

## 💻 Quick Start

Getting a SWIM node up and running requires only a few lines of code:

```python
from swim.swim import Swim

# Configure the node and its initial peers
config = {
    "local": "127.0.0.1:5700",
    "ping_timeout": 1,
    "ping_req_timeout": 1,
    "ping_req_group_size": 3,
    "hosts": [
        "127.0.0.1:5701",
        "127.0.0.1:5702"
    ]
}

swim = Swim(config)
swim.start()

print("SWIM node is now monitoring peers...")

```

## 📖 Technical Background

This implementation is based on the Cornell University research paper:

> [SWIM: Scalable Weakly-consistent Infection-style Process Group Membership Protocol](http://www.cs.cornell.edu/~asdas/research/dsn02-SWIM.pdf)

---

### Author

**Nadir Hamid** GitHub: [@nadirhamid](https://github.com/nadirhamid)

Email: matrix.nad@gmail.com
