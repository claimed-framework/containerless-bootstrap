# default code for each  operator
import os
import sys
import re
import logging

# init logger
root = logging.getLogger()
root.setLevel('INFO')
handler = logging.StreamHandler(sys.stdout)
handler.setLevel('INFO')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
logging.basicConfig(level=logging.CRITICAL)

# get parameters from args
parameters = list(filter(
                lambda s: s.find('=') > -1 and bool(re.match(r'[A-Za-z0-9_]*=[.\/A-Za-z0-9]*', s)),
                sys.argv
            ))

# set parameters to env variables
for parameter in parameters:
    variable = parameter.split('=')[0]
    value = parameter.split('=', 1)[-1]
    logging.info(f'Parameter: {variable} = "{value}"')
    os.environ[variable] = value

# update log level
log_level = os.environ.get('log_level', 'INFO')
if log_level !='INFO':
    logging.info(f'Updating log level to {log_level}')
    root.setLevel(log_level)
    handler.setLevel(log_level)
#pip install aiobotocore botocore s3fs claimed-c3


# In[ ]:


import logging
import os
import re
import s3fs
import sys
import glob
from c3.operator_utils import explode_connection_string


# In[ ]:


# cos_connection in format: [cos|s3]://access_key_id:secret_access_key@endpoint/bucket/path
cos_connection = os.environ.get('cos_connection')
(access_key_id, secret_access_key, endpoint, cos_path) = explode_connection_string(cos_connection)


# local_path for uploads, downloads, sync
local_path = os.environ.get('local_path')

# recursive
recursive = bool(os.environ.get('recursive','False'))

# operation (mkdir|ls|find|get|put|rm|sync_to_cos|sync_to_local|glob)
operation = os.environ.get('operation')

# log level
log_level = os.environ.get('log_level', 'INFO')


# In[ ]:


s3 = s3fs.S3FileSystem(
    anon=False,
    key=access_key_id,
    secret=secret_access_key,
    client_kwargs={'endpoint_url': endpoint}
)

if operation == 'mkdir':
    s3.mkdir(cos_path)
elif operation == 'ls':
    print(s3.ls(cos_path))
elif operation == 'find':
    print(s3.find(cos_path))
elif operation == 'put':
    print(s3.put(local_path,cos_path, recursive=recursive))
elif operation == 'sync_to_cos':
    for file in glob.glob(local_path, recursive=recursive):
        logging.info(f'processing {file}')
        if s3.exists(cos_path+file):
            logging.info(f'exists {file}')
            logging.debug(f's3.info {s3.info(cos_path+file)}')
            if s3.info(cos_path+file)['size'] != os.path.getsize(file):
                logging.info(f'uploading {file}')
                s3.put(file, cos_path+file)
            else:
                logging.info(f'skipping {file}')
        else:
            logging.info(f'uploading {file}')
            s3.put(file, cos_path+file)
elif operation == 'sync_to_local':
    for full_path in s3.glob(cos_path):
        local_full_path = local_path+full_path
        logging.info(f'processing {full_path}')
        if s3.info(full_path)['type'] == 'directory':
            logging.debug(f'skipping directory {full_path}')
            continue
        if os.path.exists(local_full_path):
            logging.info(f'exists {full_path}')
            logging.debug(f's3.info {s3.info(full_path)}')
            if s3.info(full_path)['size'] != os.path.getsize(local_full_path):
                logging.info(f'downloading {full_path} to {local_full_path}')
                s3.get(full_path, local_full_path)
            else:
                logging.info(f'skipping {full_path}')
        else:
            logging.info(f'downloading {full_path} to {local_full_path}')
            s3.get(full_path, local_full_path)
elif operation == 'get':
    s3.get(cos_path, local_path, recursive=recursive)
elif operation == 'rm':
    s3.rm(cos_path, recursive=recursive)
elif operation == 'glob':
    print(s3.glob(cos_path))
else:
    logging.error(f'operation unkonwn {operation}')

