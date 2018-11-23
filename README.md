# Loopchain

## Install Requirements

#### Make Virtual Env for Python 3.6.5 (recommended version, 3.7 is not supported, possible versions are 3.6.x)

 * check your python version

 ```
 $ python3 -V
 ```

 * make virtual env and apply

 ```
 $ virtualenv -p python3 ./venv
 $ source ./venv/bin/activate
 ```

 * check virtual env python version

 ```
 $ python -V
 ```

#### Install third party tools
automake, pkg-config, libtool, leveldb, rabbitmq, openssl

#### Setup RabbitMQ

* increase number of file descriptors

```
$ ulimit -S -n {value: int}
```

- Add the above command to the `rabbitmq-env.conf` file to run the command each time rabbitmq starts.
- You may find this file (/usr/local/etc/rabbitmq/rabbitmq-env.conf).
- Recommended value is 2048 or more. (Local test case only)
- You may need to adjust this value depending on your infrastructure environment.

* start rabbitmq

```
$ brew services start rabbitmq
$ rabbitmqctl list_queues
```

* enable rabbitmq web management

```
$ rabbitmq-plugins enable rabbitmq_management
```

#### Install requirements

If you have generated ssh key for github, you can install with below commands.
```
$ pip3 install git+ssh://git@github.com/icon-project/icon-service.git
$ pip3 install git+ssh://git@github.com/icon-project/icon-commons.git
$ pip3 install git+ssh://git@github.com/icon-project/icon-rpc-server.git
$ pip3 install -r requirements.txt
```

Also, you can install with below commands too.
```
$ pip3 install git+https://github.com/icon-project/icon-service.git
$ pip3 install git+https://github.com/icon-project/icon-commons.git
$ pip3 install git+https://github.com/icon-project/icon-rpc-server.git
$ pip3 install -r requirements.txt
```

#### generate gRPC code
```
$ ./generate_code.sh
```

#### Run Test

```
$ ./run_test.sh
```

## Quick Start

#### Generate Key

```
$ mkdir -p resources/my_pki
$ cd resources/my_pki
$ openssl ecparam -genkey -name secp256k1 | openssl ec -aes-256-cbc -out my_private.pem    # generate private key
$ openssl ec -in my_private.pem  -pubout -out my_public.pem                                # generate public key
$ export PW_icon_dex={ENTER_MY_PASSWORD}
$ cd ../../
```

#### Write channel_manage_data.json for private loopchain network

* It is necessary to execute loopchain privately.
* Radiostation must have this file.
* Peer does not need this.
* It's quite simple.

Format

```
{
  "[CHANNEL_NAME]": {
    "score_package": "score/icx",
    "peers": [
      {
        "peer_target": "[PEER_IP]:[PEER_PORT]"
      },
      ...
    ]
  },
  ...
}
```

Example for local test

```
{
  "icon_dex": {
    "score_package": "score/icx",
    "peers": [
      {
        "peer_target": "[local_ip]:7100"
      },
      {
        "peer_target": "[local_ip]:7200"
      },
      {
        "peer_target": "[local_ip]:7300"
      },
      {
        "peer_target": "[local_ip]:7400"
      },
      {
        "peer_target": "[local_ip]:7900"
      },
      {
        "peer_target": "[local_ip]:8100"
      }
    ]
  },
  "loopchain_test": {
    "score_package": "loopchain/default",
    "peers": [
      {
        "peer_target": "[local_ip]:7100"
      },
      {
        "peer_target": "[local_ip]:7200"
      },
      {
        "peer_target": "[local_ip]:7300"
      },
      {
        "peer_target": "[local_ip]:7500"
      },
      {
        "peer_target": "[local_ip]:8000"
      },
      {
        "peer_target": "[local_ip]:8200"
      }
    ]
  }
}
```

#### Run loopchain as a radiostation

```
$ ./loopchain.py rs
```

#### Run loopchain as a peer

```
$ ./loopchain.py peer -r {RADIOSTATION_IP:PORT} -o conf/{PEER_CONFIG}.json
```

#### Run Local Test with RS and 4 Peers

```
$ ./loopchain.py rs

$ ./loopchain.py peer -r 127.0.0.1:7102 -o conf/test_0_conf.json

$ ./loopchain.py peer -r 127.0.0.1:7102 -o conf/test_1_conf.json

$ ./loopchain.py peer -r 127.0.0.1:7102 -o conf/test_2_conf.json

$ ./loopchain.py peer -r 127.0.0.1:7102 -o conf/test_3_conf.json
```

#### Run loopchain as a Citizen Node

```
$ ./run_loopchain.sh
```

#### Stop All

```
# This script does not support all platforms and may need to be modified. (Please refer to the script.)
$ ./stop_all.sh
```

#### Clean Up (delete log / delete DB)

```
$ rm -rf log
$ rm -rf .storage_test
```