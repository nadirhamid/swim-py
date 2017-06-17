SWIM in Python
===========================================================

A basic integration of the SWIM distribution strategy and
"suspect" based failure detection.

This module includes most of the functionality in SWIM. And
it serves a very good example for prototyping SWIM. This 
module could be of use to you if:

- You are unsure if SWIM is the correct failure detection to use and
you want to test it's failure detection rate.
- You would like to learn more about how SWIM works
- You are familiar with SWIM and could not find a Python module that integrates it.

Requirements
=========================================================
```
Python 2.7
```

Installation
=========================================================

```
python setup.py build
python setup.py install
```

Creating a SWIM instance
========================================================
```
from swim.swim import Swim

swim = Swim({
        "local": "127.0.0.1:5700",
        "ping_timeout": 1,
        "ping_req_timeout": 1,
        "ping_req_group_size": 3,
        "hosts": [
            "127.0.0.1:5701",
            "127.0.0.1:5702"
        ]
})
swim.start()
```

Credits
=========================================================

This is based on
http://www.cs.cornell.edu/~asdas/research/dsn02-SWIM.pdf

Module Author

Nadir Hamid (matrix.nad@gmail.com)
