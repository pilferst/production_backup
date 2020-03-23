import paramiko
import os
import yaml
import time
import datetime
from  concurrent.futures import ThreadPoolExecutor
import scp




def dir_check(hostname):
    link="/home/python/scripts/production_backup/backup_files/"
    if not os.path.exists(link + hostname):
        os.makedirs(link + hostname)

    return None


def export_device(router):
#    print("export", router[0], router[1])
#    print("export", router[0], router[1], credentionals["username"], credentionals["password"],credentionals["port"])
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
        fail=current_date+'-backup-export-fail'
        with open(link + device[0] + '/' + fail, "w") as file_write:
            file_write.write(fail)
        return None

def backup_device(router):
#    print("backup", router[0], router[1])
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
        fail=current_date+'-backup-fail'
        with open(link + device[0] + '/' + fail, "w") as file_write:
            file_write.write(fail)
    return None

def concurrent_export_device(routers, limit):
#    print("concurrent_export_device",credentionals,list(routers))
    with ThreadPoolExecutor(max_workers=limit) as executor:
        f_result = executor.map(export_device, routers)

    return None


def concurrent_backup_device(routers, limit):
#    print("concurrent_backup_device")
    with ThreadPoolExecutor(max_workers=limit) as executor:
        backup_result = executor.map(backup_device, routers)

    return None

def delete_old_files(router):
    link="/home/python/scripts/production_backup/backup_files/"+router+"/"
#    print(link)
    max_files=10
    list_export=[]
    list_backup=[]

    for id in os.listdir(link):
        if ".export" in id:
            list_export.append((id,os.stat(link+id).st_mtime))
        elif ".backup" in id:
            list_backup.append((id,os.stat(link+id).st_mtime))
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




if __name__ == "__main__":
    limit=32
    credentionals={}
    current_date=datetime.datetime.today().strftime('%d-%m-%Y')

    with open ("credentionals.yml","r") as file_read:
        temp_credentionals=yaml.safe_load(file_read)
    for id in temp_credentionals:
        credentionals.update(id)
#    print(credentionals)

    with open ("routers.yml","r") as file_read:
        routers=yaml.safe_load(file_read)
    routers=list(routers.items())

    for id in routers:
        dir_check(id[0])

    concurrent_export_device(routers, limit)
    concurrent_backup_device(routers, limit)

    try:
        for id in routers:
            delete_old_files(id[0])
    except:
        pass






