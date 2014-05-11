#!/usr/bin/env python

import httplib2
import json

class Lxc(object):

    def __init__(self):

        self.url = 'http://10.0.3.1:5000'
        self.http = httplib2.Http()
        self.headers = {'Content-type': 'application/json'}

    def create_server(self,hostname,size=1,image="jbase"):

        url = self.url + "/server/create"
    
        body = { "hostname":hostname, "size": size, "image": image }
    
        jsonarray = json.dumps(body)
    
        response, content = self.http.request(url, 'POST', headers=self.headers, body=jsonarray)
    
        if int(dict(response)["status"]) == 200:
            print "Post for server creation submitted for %s" % body
            content = json.loads(content)
            return content
        else:
            print "Post for server creation failed for %s" % body

    def destroy_server(self,hostname):

        url = self.url + "/server/destroy"
    
        body = { "hostname":hostname }
    
        jsonarray = json.dumps(body)
    
        response, content = self.http.request(url, 'POST', headers=self.headers, body=jsonarray)
    
        if int(dict(response)["status"]) == 200:
            print "Post for server deletion submitted for %s" % body
            return content
        else:
            print "Post for server deletion failed for %s" % body

if __name__ == "__main__":
    hresponse = Lxc().create_server("test-app1")
    print hresponse
    
