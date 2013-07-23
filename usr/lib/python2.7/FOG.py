#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 FOG.py
 Description : FOG GNU/Linux pseudo client service
 Version : 0.2

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>

"""

import os, re, sys, socket, syslog, subprocess
from httplib2 import Http
from urllib import urlencode
from base64 import b64encode

class client(object):

	def __init__(self):
        	self.syslog=True
    		self.verbose=False
    		self.debug=False
    		self.http=Http()
    		self.host="http://172.16.106.90/"
    		self.serv={
            		"hostlookupbymac":'fog/service/hostlookupbymac.php',
            		"jobs":'fog/service/jobs.php',
            		"usertracking":'fog/service/usertracking.report.php'
    		}
    		self.ret={
            		"#!ok": 'Ok',
            		"#!db": 'Database Error',
            		"#!im": 'Invalid MAC Format',
            		"#!ih": 'Invalid Hostname',
		    	"#!il": 'Not Found',
		    	"#!er": 'Other Error',
		    	"#!nf": 'Not Found',
		    	"#!nj": 'No Jobs',
		    	"#!ac": 'Invalid Action Command',
		    	"#!nh": 'Host Not Found',
		    	"#!us": 'Invalid User'
		}
 	
		if self.syslog : syslog.openlog(sys.argv[0],syslog.LOG_PID,syslog.LOG_DAEMON)

	def _exit(self,msg):
		if self.verbose: print(msg)
		if self.syslog : syslog.syslog(syslog.LOG_INFO,msg)
		if self.debug  : import pdb; pdb.set_trace()
		sys.exit(1)

    	def _msg(self,msg):
		if self.verbose: print(msg)
		if self.syslog: syslog.syslog(syslog.LOG_ERR,msg)

    	def _getMac(self,nic='eth0'):
        	MAC = '([a-fA-F0-9]{2}[:|\-]?){6}'
		stdout_lines = subprocess.Popen('/sbin/ifconfig',shell=True,stdout=subprocess.PIPE,stderr=open(os.devnull,'w')).communicate()[0].split("\n")
		for line in stdout_lines:
			if nic in line and 'HWaddr' in line:
                		MACpos = re.compile(MAC).search(line)
        		if MACpos:
                		return(line[MACpos.start(): MACpos.end()])

    	def _getSHostName(self):
		try:
        		return(str(socket.gethostbyaddr(socket.gethostname())[0].split('.')[0]))
    		except:
			return("localhost.localdomain")

    	def _getUserName(self):
        	return(os.getenv('USER'))

    	def _computerUsed(self,tty='tty7'):
        	stdout = subprocess.Popen('/usr/bin/who',shell=True,stdout=subprocess.PIPE,stderr=open(os.devnull,'w')).communicate()[0]
       		if tty in stdout:
            		return(True)
        	else:
            		return(False)

    	def _getFHostName(self):
		url = self.host+self.serv["hostlookupbymac"] #TODO: dealing whith the good serverside php script using GET request.
	    	body = {'mac': self._getMac()}
	    	headers = {'Content-type': 'application/x-www-form-urlencoded'}
	    	resp,c=self.http.request(url,'POST',headers=headers,body=urlencode(body))
	    	if self.debug: print(url,sys.argv,resp,c)

	    	if c in self.ret:
	        	self._exit(self.ret[c])
	    	else :
	        	c.strip('  ')
	       		c=c.split('  ')
	        	c=c[1].split(':')
	        	c=c[1].strip('\\n')
	        	c=c.lstrip()
	        	return(c)

    	def setHostName(self):
	    	try:
			c=self._getFHostName()
	    	except:
		    	self._exit("Can't get hostame")
	    	try:
		    	hnf=open('/etc/hostname','w')
	    	except:
		    	self._exit("Can't write /etc/hostname")

	    	hnf.write(c)
	    	hnf.close()

        	try:
		    hf=open('/etc/hosts', 'w')
	    	except:
		    self._exit("Can't write /etc/hosts")

	    	hf.writelines(["127.0.0.1 localhost.localdomain "+c+" localhost\n","127.0.0.1 "+c.lower()+".domain.tld"])
	    	hf.close()
	    	#popen hostname -f NetworkManager # Slower
	    	subprocess.Popen('/bin/hostname -F /etc/hostname',shell=True)
	    	self._msg('Set Hostname to : '+c.lower())

    	def ontaskReboot(self):
		url=self.host+self.serv["jobs"]+"?mac="+self._getMac()
	    	resp,c=self.http.request(url,"GET")
	    	if self.debug: print(url,sys.argv,resp,c)
	    	resp=dict(resp)

	    	if c=="#!ok":
	        	if not self._computerUsed():
		    		subprocess.Popen('/sbin/reboot',shell=True,stdout=open(os.devnull,'w'),stderr=open(os.devnull,'w'))
		    		self._msg('Reboot')
	    		else:
	        		self._msg(self.ret[c])

    	def userTracking(self):
		try:
			mac=b64encode(self._getMac())
	    	except:
			Self._exit('No MAC Found')
		try:
		 	action=b64encode(sys.argv[1])
	    	except:
		   	self._exit('Missing Argument Login/Logout')

	    	try:
			user=b64encode(self._getFHostName()+'\\'+self._getUserName())
	    	except:
			self._exit("Either Hostname: '"+self._getFHostName()+"' or Username: '"+self._getUserName()+"' not define")

	    		date=''
	    		url=self.host+self.serv["usertracking"]+'?mac='+mac+'&action='+action+'&user='+user+'&date='+date
	    		resp,c=self.http.request(url,"GET")
	    		if self.debug: print(url,sys.argv,resp,c)

	    		if c=="#!ok":
	        		self._msg('User Tracking OK')
	    		else:
	        		self._msg(self.ret[c])

