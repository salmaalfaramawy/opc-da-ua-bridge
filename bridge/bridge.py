import queue
import logging
from datetime import datetime

import opcua
from opcua import ua
import OpenOPC

from config import CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def DARead(da_client, group_name):
    tags = [tag for tag in da_client.list(flat=True) if tag.startswith(group_name)]

    opcua_tagname_list = [tag[tag.rfind('.') + 1:] for tag in tags]

    values_lst = [(value, timestamp) for name, value, quality, timestamp in da_client.read(tags)]
    access_lst = [acc for name, acc in da_client.properties(tags, id=5)]
    dtypes_lst = [dtype for name, dtype in da_client.properties(tags, id=1)]

    values=dict(zip(opcua_tagname_list, values_lst))
    accesss=dict(zip(opcua_tagname_list, access_lst))
    dtypes=dict(zip(opcua_tagname_list, dtypes_lst))

    return values,accesss, dtypes

def opcua_setup(object_name:str, endpoint: str, namespace_uri: str):
    opcua_server=opcua.Server()
    opcua_server.set_endpoint(endpoint)

    index = opcua_server.register_namespace(namespace_uri)
    objects_node=opcua_server.get_objects_node()

    obj=objects_node.add_object(index, object_name)

    return index, opcua_server, obj

def ua_tag_create (obj:opcua.Node, index:int, opcua_tag_dict:dict, access_dict:dict,
                   subscription:opcua.Subscription, dtype_dict:dict, ua_r_and_rw:dict):
    dtype_mapping={
        '2':ua.NodeId(ua.ObjectIds.Int16),
        '3': ua.NodeId(ua.ObjectIds.Int32),
        '4': ua.NodeId(ua.ObjectIds.Float),
        '5': ua.NodeId(ua.ObjectIds.Double),
        '7': ua.NodeId(ua.ObjectIds.DateTime),
        '8': ua.NodeId(ua.ObjectIds.String),
        '11':ua.NodeId(ua.ObjectIds.Boolean),
        '14':ua.NodeId(ua.ObjectIds.Decimal),
        '16':ua.NodeId(ua.ObjectIds.SByte),
        '17':ua.NodeId(ua.ObjectIds.Byte),
        '18':ua.NodeId(ua.ObjectIds.UInt16),
        '19':ua.NodeId(ua.ObjectIds.UInt32),
        '20':ua.NodeId(ua.ObjectIds.Int64),
        '21': ua.NodeId(ua.ObjectIds.UInt64)
    }
    for ua_tagname in access_dict.keys():
        if ua_tagname not in opcua_tag_dict.keys():

            dtype=dtype_mapping[str(dtype_dict[ua_tagname])]

            new_var=obj.add_variable(index, ua_tagname,val=0, datatype=dtype)

            if  access_dict[ua_tagname] in ('Read/Write','Write'):

                new_var.set_writable()
                subscription.subscribe_data_change(new_var)

                if access_dict[ua_tagname]=='Read/Write':
                    ua_r_and_rw.update({ua_tagname:new_var})
            else:
                ua_r_and_rw.update({ua_tagname:new_var})

            opcua_tag_dict.update({ua_tagname:new_var})
            logging.info(f"Created UA tag: {ua_tagname}")

class OPCUAHandler:
    def __init__(self,opcua_tags:dict, group_name:str):
        self.opcua_tags=opcua_tags
        self.group_name=group_name
        self.queue=queue.Queue()

    def datachange_notification(self, node:opcua.Node, val,data):
        for ua_tagname,tag in self.opcua_tags.items():
            if tag==node:
                da_tagname=f'{self.group_name}.{ua_tagname}'
                self.queue.put((ua_tagname,da_tagname, val))

def UA2DA_Write(UAHandler:OPCUAHandler, da_client:OpenOPC.client, ua_last_write:dict, da_last_read:dict):
    if not UAHandler.queue.empty():
        ua_tagname, da_tagname, value=UAHandler.queue.get(timeout=0.1)
        if value!= da_last_read.get(ua_tagname, None):
            da_client.write((da_tagname, value))
            ua_last_write.update({ua_tagname:value})
            logging.info(f"WRITE UA → DA: {ua_tagname} = {value}")

def DA2UAWrite(ua_r_and_rw:dict, values, ua_last_write:dict, da_last_read:dict):
    for ua_tagname,tag in ua_r_and_rw.items():
        if ua_tagname in ua_last_write.keys():
            if values[ua_tagname][0]!=ua_last_write[ua_tagname]:
                timestamp=datetime.fromisoformat(values[ua_tagname][1])
                tag.set_value(ua.DataValue(variant=values[ua_tagname][0],
                                           serverTimestamp=datetime.now(),
                                           sourceTimestamp=timestamp))
                logging.info(f"WRITE DA → UA: {ua_tagname} = {values[ua_tagname][0]}")

        elif da_last_read.get(ua_tagname, None)!=values[ua_tagname][0]:
            timestamp = datetime.fromisoformat(values[ua_tagname][1])
            tag.set_value(ua.DataValue(variant=values[ua_tagname][0],
                                       serverTimestamp=datetime.now(),
                                       sourceTimestamp=timestamp))
            logging.info(f"WRITE DA → UA: {ua_tagname} = {values[ua_tagname][0]}")

        da_last_read.update({ua_tagname:values[ua_tagname][0]})

def main():
    da_client = OpenOPC.client()
    da_client.connect(CONFIG["da_server"])

    index, ua_server, obj = opcua_setup(
        CONFIG["ua_object_name"],
        CONFIG["endpoint"],
        CONFIG["namespace_uri"]
    )

    ua_server.start()


    ua_tag_dict = {}
    handler = OPCUAHandler(ua_tag_dict, CONFIG["group_name"])
    subscription=ua_server.create_subscription(500, handler)

    ua_r_and_rw={}
    ua_last_write = {}
    da_last_read = {}

    try:
        while True:
            UA2DA_Write(handler, da_client, ua_last_write, da_last_read)

            values,accesss,dtypes=DARead(da_client,CONFIG["group_name"])

            ua_tag_create(
                obj, index, ua_tag_dict,
                accesss, subscription,
                dtypes, ua_r_and_rw
            )

            DA2UAWrite(ua_r_and_rw, values, ua_last_write,da_last_read)

    except KeyboardInterrupt:
        logging.info("Shutting down bridge...")

    finally:
        da_client.close()
        ua_server.stop()


if __name__=="__main__":
    main()
