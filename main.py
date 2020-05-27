"""This module get backups form routers. There are two type of backups. The frist one is a text file. The second one is binary file. If the module see in a dictorinary more than 10 files, the module delete reast of them. """
import paramiko
import os
import yaml
import time
import datetime
from  concurrent.futures import ThreadPoolExecutor
import scp
from typing import Tuple
from typing import Dict
from typing import List
from typing import Any

def dir_check(hostname: str) -> None:
    link : str

    link="/home/python/scripts/production_backup/backup_files/"
    if not os.path.exists(link + hostname):
        os.makedirs(link + hostname)
    return None


def export_device(router: Tuple[str,str] ) -> None:
    link : str
    current_date : str
    command : str
    fail : str
    global credentionals


    link="/home/python/scripts/production_backup/backup_files/"
    current_date=datetime.datetime.today().strftime('%d-%m-%Y')
    command='/export'
    try:

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=router[1], username=credentionals["username"], password=credentionals["password"], port=credentionals["port"], look_for_keys=False, allow_agent=False)
        stdin,stdout,stderr = client.exec_command(command)
        backup_config=stdout.read().decode('utf-8')
        client.close()
        with open(link + router[0] + '/'+current_date + ".export", "w") as file_write:
            file_write.write(backup_config)
        return None

    except:
        fail='Backup-export-fail'
        with open(link + router[0] + '/' + fail, "w") as file_write:
            file_write.write(fail)
        return None

def backup_device(router: Tuple[str,str]) -> None:
    link : str
    current_date : str
    command : str
    fail : str
    global credentionals

    link="/home/python/scripts/production_backup/backup_files/"
    current_date=datetime.datetime.today().strftime('%d-%m-%Y')
    command='/system backup save dont-encrypt=yes name=Daily-'+current_date
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=router[1], username=credentionals["username"], password=credentionals["password"], port=credentionals["port"], look_for_keys=False, allow_agent=False, timeout=5)
        stdin,stdout,stderr = client.exec_command(command)
        time.sleep(5)
        download=scp.SCPClient(client.get_transport())
        download.get('Daily-'+current_date+'.backup', link + router[0]+'/'+current_date+".backup")
        download.close()
        time.sleep(5)
        command_remove='/file remove Daily-'+current_date+'.backup'
        time.sleep(3)
        stdin,stdout,stderr = client.exec_command(command_remove)
        client.close()

    except:
        fail='Backup-fail'
        with open(link + router[0] + '/' + fail, "w") as file_write:
            file_write.write(fail)
    return None

def concurrent_export_device(routers : List[Tuple[str,str]], limit : int ) -> None:
    with ThreadPoolExecutor(max_workers=limit) as executor:
        f_result = executor.map(export_device, routers)
    return None


def concurrent_backup_device(routers : List[Tuple[str,str]], limit : int) -> None :
    with ThreadPoolExecutor(max_workers=limit) as executor:
        backup_result = executor.map(backup_device, routers)
    return None

def delete_old_files(router: str ) -> None:
    link : str
    max_files : int
    list_export: List[Tuple[str,float]]
    list_backup: List[Tuple[str,float]]


    link="/home/python/scripts/production_backup/backup_files/"+router+"/"
    max_files=10
    list_export=[]
    list_backup=[]

    for id in os.listdir(link):
        if ".export" in id:
            list_export.append((id,os.stat(link+id).st_mtime))
            os.chmod(link + id, 0o444)
        elif ".backup" in id:
            list_backup.append((id,os.stat(link+id).st_mtime))
            os.chmod(link + id, 0o444)
    list_export=sorted(list_export, key = lambda x : x[1])
    list_backup=sorted(list_backup, key = lambda x : x[1])

    if len(list_export)>max_files:
        del_list_export=list_export[:len(list_export)-max_files]
        for id_del in del_list_export:
            os.remove(link + id_del[0])

    if len(list_backup)>max_files:
        del_list_backup=list_backup[:len(list_backup)-max_files]
        for id_del in del_list_backup:
            os.remove(link + id_del[0])
    return None


if __name__ == "__main__":
    limit : int
    credentionals : Dict[str,str]
    routers : List[Tuple[str,str]]

    limit=32
    credentionals={} 
    current_date=datetime.datetime.today().strftime('%d-%m-%Y')

    with open ("/home/python/scripts/production_backup/credentionals.yml","r") as file_read:
        temp_credentionals=yaml.safe_load(file_read)
    for id in temp_credentionals:
        credentionals.update(id)

    with open ("/home/python/scripts/production_backup/routers.yml","r") as file_read:
        routers_dict=yaml.safe_load(file_read)
    routers=list(routers_dict.items())

    for id in routers:
        dir_check(id[0])

    concurrent_export_device(routers, limit)
    concurrent_backup_device(routers, limit)

    try:
        for id in routers:
            delete_old_files(id[0])
    except:
        pass
