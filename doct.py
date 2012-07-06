import numpy as np
import acquirer
import logging
from configobj import ConfigObj
from validate import Validator

flags = [
    'calibrate-spectrum',
    'scan-continuous',
    'scan-single',
    'scan-3D',
    'x',
    'get-p',
    'resample-d',
    'transform',
    'non-cor-fft',
    'line',
    'load',
    'store',
    'plot',
    'img-plot',
    ]

def parse():
    import argparse
    parser = argparse.ArgumentParser()
    parser.description = "OCT client."
    parser.add_argument('-o', dest='filename', default='data.dat')
    for flag in flags:
        parser.add_argument('--' + flag,action='store_true') 
    return parser.parse_args()

arg = parse()
validator = Validator({'log':acquirer.log_type,'float':float})
config = ConfigObj('config.ini',configspec='configspec.ini')
if not config.validate(validator):
    raise Exception('config.ini does not validate with configspec.ini.')
logging.basicConfig(level=config['log'])

data = []
config['filename'] = arg.filename
logging.info('Writing data in %s'%config['filename'])
    
for i in flags:
    function_name = i.replace('-','_')
    if getattr(arg, function_name):
        logging.info("Executing %s"%function_name)
        fun = getattr(acquirer, function_name)
        data = fun(config, data)    


