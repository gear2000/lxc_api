#!/usr/bin/env python

from flask import request, url_for,jsonify
from flask.ext.api import FlaskAPI, status, exceptions
import string
from time import time,sleep
from itertools import chain
from random import seed, choice, sample, randrange
import json
import subprocess

app = FlaskAPI(__name__)

@app.route('/server/create', methods = ['POST'])
def create_server():

    if not request.json:
        print "format isn't in json"
        abort(400)

    input = dict(request.json)
    hostname = input["hostname"]
    size = input["size"]
    image = input["image"]

    public_ips,private_ips,passwd = lxc_create(hostname,image,size,passwd=None)

    server_id = _mkpasswd(length=10, digits=7, upper=0, lower=2)

    server_params = { "hostname":hostname, \
    "public_ips" : public_ips, \
    "private_ips" : private_ips, \
    "password" : passwd, \
    "id" : server_id \
    }

    jsonify(server_params)

@app.route('/server/destroy', methods = ['POST'])
def destroy_server():

    if not request.json:
        print "format isn't in json"
        abort(400)

    input = dict(request.json)
    hostname = input["hostname"]

    status = lxc_destroy(hostname)

    jsonify({"status" : status})

def lxc_destroy(hostname):
    
    cmd = "lxc stop %s" % (hostname)
    _execute(cmd)

    sleep(5)

    cmd = "lxc destroy %s" % (hostname)
    status = _execute(cmd)

    if status: return True

def lxc_create(hostname,image,size,passwd=None):

    if not passwd:
        passwd = _mkpasswd()

    cmd = "openssl passwd -1 %s" % passwd
    passwd_hash = _execute(cmd)
    
    cmd = "lxc-clone -o %s -n %s" % (image,hostname)
    _execute(cmd)

    cmd = "ssh-keygen -f /var/lib/lxc/%s/rootfs/etc/ssh/ssh_host_rsa_key -N \'\' -t rsa" % hostname
    _execute(cmd)

    cmd = "ssh-keygen -f /var/lib/lxc/%s/rootfs/etc/ssh/ssh_host_dsa_key -N \'\' -t dsa" % hostname
    _execute(cmd)

    memory = _size(size)

    cmd = 'echo "lxc.cgroup.memory.limit_in_bytes = %s" >> /var/lib/lxc/%s/config' % (memory,hostname)
    _execute(cmd)

    netfile,public_ips,private_ips = _create_net()

    netwrite = open("/var/lib/lxc/%s/rootfs/etc/network/interfaces" % hostname, "w")
    netwrite.write(netfile)
    netwrite.close

    cmd = "lxc start %s -d" % (hostname)
    _execute(cmd)

    return public_ips,private_ips,passwd
    
def _create_net():

    public_base = "192.168.1"
    private_base = "10.0.3"

    random_num = randrange(150, 199, 1)

    public_ips = "{}.{}".format(public_base,random_num)
    private_ips = "{}.{}".format(private_base,random_num)

    netfile = """
# This file describes the network interfaces available on your system
# and how to activate them. For more information, see interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback

# The primary network interface
auto eth0
iface eth0 inet static
    address {pub_base}.{num}
    netmask 255.255.255.0
    network {pub_base}.0
    broadcast {pub_base}.255
    gateway {pub_base}.1
    # dns-* options are implemented by the resolvconf package, if installed
    dns-nameservers {pub_base}.1

auto eth1
iface eth1 inet static
    address {prv_base}.{num}
    netmask 255.255.255.0
    network {prv_base}.0
    broadcast {prv_base}.255
""".format(pub_base=public_base,prv_base=private_base,num=random_num)

    return netfile,public_ips,private_ips


def _execute(cmd):

    '''executes a shell command, returning status of execution,
    standard out, and standard error'''

    print "Running command %s" % cmd

    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, error = process.communicate()

    print "exit status %s" % process.returncode

    if process.returncode == 0:
       print "standard output: \n%s" % out
    else:
       print "standard error: \n%s" % error
       exit(278)

    return out

def _size(size):

    sizes = { 1 : "512M", 2 : "1G", 3 : "2G", 4 : "4G", 5 : "8G" }

    return sizes[int(size)]

#took off of stackoverflow
def _mkpasswd(length=8, digits=2, upper=2, lower=2):
    """Create a random password

    Create a random password with the specified length and no. of
    digit, upper and lower case letters.

    :param length: Maximum no. of characters in the password
    :type length: int

    :param digits: Minimum no. of digits in the password
    :type digits: int

    :param upper: Minimum no. of upper case letters in the password
    :type upper: int

    :param lower: Minimum no. of lower case letters in the password
    :type lower: int

    :returns: A random password with the above constaints
    :rtype: str
    """

    seed(time())

    lowercase = string.lowercase.translate(None, "o")
    uppercase = string.uppercase.translate(None, "O")
    letters = "{0:s}{1:s}".format(lowercase, uppercase)

    password = list(
        chain(
            (choice(uppercase) for _ in range(upper)),
            (choice(lowercase) for _ in range(lower)),
            (choice(string.digits) for _ in range(digits)),
            (choice(letters) for _ in range((length - digits - upper - lower)))
        )
    )

    return "".join(sample(password, len(password)))

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')


