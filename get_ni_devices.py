from subprocess import Popen, PIPE

cmd = ['nilsdev']
#cmd = ['nilsdev', '|', 'grep', '-v "Not Present"']
out = Popen(cmd, stdout = PIPE)
lines =  out.stdout.readlines()
lines = [line.strip('\n') for line in lines]
present_devices = {}
for line in lines:
    if line.rfind('Not Present') == -1 and line != '':
        devices = line.split(' ')
        present_devices[devices[1].strip(':')] = devices[2]
