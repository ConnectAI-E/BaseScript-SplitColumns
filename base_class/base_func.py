from baseopensdk import BaseClient
from baseopensdk.api.base.v1 import *
import os, json
from flask import render_template


## 获取多维表格中的数据表列表 ##
def list_tables_func(APP_TOKEN: str, PERSONAL_BASE_TOKEN: str):

  try:
    # 1. 构建client
    client: BaseClient = BaseClient.builder() \
      .app_token(APP_TOKEN) \
      .personal_base_token(PERSONAL_BASE_TOKEN) \
      .build()

    # 2. 获取多维表格的数据表列表
    list_tables_request = ListAppTableRequest.builder() \
      .page_size(100) \
      .build()

    list_tables_response = client.base.v1.app_table.list(list_tables_request)
    tables = getattr(list_tables_response.data, 'items') or []

    tables_list = []
    for table in tables:
      # print(table.__dict__, flush=True)
      tables_list.append({
          "table_id": table.table_id,
          "table_name": table.name
      })

    TABLE_ID = tables_list[0].get("table_id")

    fields_list = list_fields_func(APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID)
    # print(fields_list, flush=True)

    return {"tables_list": tables_list, "fields_list": fields_list}

    print('数据表列表获取成功!', flush=True)

  except Exception as e:
    print('数据表列表获取错误!', flush=True)
    raise ('数据表列表获取错误!')


## 列出所选数据表的可选字段信息 ##
def list_fields_func(APP_TOKEN: str, PERSONAL_BASE_TOKEN: str, TABLE_ID: str):

  try:
    # 1. 构建client
    client: BaseClient = BaseClient.builder() \
      .app_token(APP_TOKEN) \
      .personal_base_token(PERSONAL_BASE_TOKEN) \
      .build()

    # 2. 获取抽奖人员信息表的字段信息
    list_field_request = ListAppTableFieldRequest.builder() \
      .page_size(100) \
      .table_id(TABLE_ID) \
      .build()

    list_field_response = client.base.v1.app_table_field.list(
        list_field_request)
    fields = getattr(list_field_response.data, 'items') or []

    fields_list = []
    for field in fields:
      # print(field.__dict__, flush=True)
      if field.ui_type == 'Text':
        fields_list.append({
            "field_id": field.field_id,
            "field_name": field.field_name
        })

    return fields_list

    print('字段列表获取成功!', flush=True)

  except Exception as e:
    print('字段列表获取错误!', flush=True)
    raise ('字段列表获取错误!')


## 开始分列操作 ##
def update_data_func(APP_TOKEN: str, PERSONAL_BASE_TOKEN: str, TABLE_ID: str,
                     FIELD_NAME: str, SEPARATOR: str):

  try:
    # 1. 构建client
    client: BaseClient = BaseClient.builder() \
      .app_token(APP_TOKEN) \
      .personal_base_token(PERSONAL_BASE_TOKEN) \
      .build()
  
    # 2. 遍历记录
    list_record_request = ListAppTableRecordRequest.builder() \
      .page_size(500) \
      .field_names('["' + FIELD_NAME + '"]') \
      .filter("") \
      .table_id(TABLE_ID) \
      .page_token("") \
      .build()
  
    # print(list_record_request.__dict__, flush=True)
  
    list_record_response = client.base.v1.app_table_record.list(
        list_record_request)
    records = getattr(list_record_response.data, 'items', [])
  
    data_list = []
  
    for record in records:
      # print(record.__dict__, flush=True)
      fields = record.fields
      # print(fields, flush=True)
      for key, value in fields.items():
        # print(value, flush=True)
        data_list.append({
              "record_id": record.record_id,
              "data": value
          })
  
    has_more = list_record_response.data.has_more
    page_token = list_record_response.data.page_token
  
    while has_more:
      list_record_request = ListAppTableRecordRequest.builder() \
        .page_size(500) \
        .field_names('["' + FIELD_NAME + '"]') \
        .filter("") \
        .table_id(TABLE_ID) \
        .page_token(page_token) \
        .build()
  
      list_record_response = client.base.v1.app_table_record.list(
          list_record_request)
      records = getattr(list_record_response.data, 'items', [])
  
      has_more = list_record_response.data.has_more
      page_token = list_record_response.data.page_token
  
      for record in records:
        fields = record.fields
        for key, value in fields.items():
          data_list.append({
              "record_id": record.record_id,
              "data": value
          })
  
    # print(data_list, flush=True)
  
    import re
    # print(SEPARATOR, flush=True)
    # #| |\\|/|\,|\|
    value_len = 0
    max_num = 0
    curr_num = 0
    records_update = []
    for value in data_list:
      # value_list = value.split(SEPARATOR)
      NEW_FIELD_NAME_PRE = FIELD_NAME + "_分列字段"
      NEW_FIELD_NAME = ""
      value_list = value.get("data")
      value_list = re.split(SEPARATOR, value_list)
  
      # print(value_list, flush=True)
      if len(value_list) > value_len:
        value_len = len(value_list)
        curr_num = value_len - max_num
        for i in range(max_num + 1, value_len + 1):
          NEW_FIELD_NAME = NEW_FIELD_NAME_PRE + str(i)
          max_num = len(value_list)  
      
      ## 拼接更新记录的字符串 ##
      record_id = value.get("record_id")
      result = join_fields_list_func(APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID,
                             NEW_FIELD_NAME_PRE, record_id, value_list)
      records_update.append(result)
     
    create_filed_func(APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID,
                            NEW_FIELD_NAME_PRE, max_num)
    # print(records_update,flush=True)

    ## 更新拆分的数据到新字段 ##
    update_field_func(APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID,
                             records_update)
    print('数据分列完成!')
    return {"code": 200, "msg": "数据分列完成!"}

  except Exception as e:
    return {"code": -1, "msg": "参数错误!"}
    # raise ('参数错误!')

## 拼接更新记录的字符串 ##
def join_fields_list_func(APP_TOKEN: str, PERSONAL_BASE_TOKEN: str,
                         TABLE_ID: str, FIELD_NAME: str, RECORD_ID: str, VALUE_LIST: list):

  update_record = {}
  update_fields = {}
  update_fields_item = {}

  for index in range(len(VALUE_LIST)):
    new_field_name = FIELD_NAME + str(index + 1)
    value =  VALUE_LIST[index]
    update_fields_item[new_field_name] = value
  
  update_record["record_id"] = RECORD_ID
  update_record["fields"] = update_fields_item

  return update_record


## 保存记录到对应字段 ##
def update_field_func(APP_TOKEN: str, PERSONAL_BASE_TOKEN: str,
                         TABLE_ID: str, RECORDS_UPDATE):

  # print(RECORDS_UPDATE, flush=True)
  
  # 1. 构建client
  client: BaseClient = BaseClient.builder() \
      .app_token(APP_TOKEN) \
      .personal_base_token(PERSONAL_BASE_TOKEN) \
      .build()

  # 2. 保存数据信息到字段
  batch_update_records_request = BatchUpdateAppTableRecordRequest().builder() \
  .table_id(TABLE_ID) \
  .request_body(
    BatchUpdateAppTableRecordRequestBody.builder() \
      .records(RECORDS_UPDATE) \
      .build()
  ) \
  .build()

  batch_update_records_response = client.base.v1.app_table_record.batch_update(
      batch_update_records_request)

  print('数据保存成功!', flush=True)


## 创建新字段 ##
def create_filed_func(APP_TOKEN: str, PERSONAL_BASE_TOKEN: str, TABLE_ID: str,
                      FIELD_NAME: str, MAX_NUM: int):
  
  try:
    # 1. 构建client
    client: BaseClient = BaseClient.builder() \
      .app_token(APP_TOKEN) \
      .personal_base_token(PERSONAL_BASE_TOKEN) \
      .build()

    for index in range(1, MAX_NUM + 1):
      # 2. 创建新字段，例如【数据字段名称_分列字段1】【数据字段名称_分列字段2】
      create_field_request = CreateAppTableFieldRequest().builder() \
      .table_id(TABLE_ID) \
      .request_body(
        AppTableField.builder() \
          .field_name(FIELD_NAME + str(index)) \
          .type(1) \
          .build()
      ) \
      .build()
  
      create_field_response = client.base.v1.app_table_field.create(
          create_field_request)
  
      print('【' + FIELD_NAME + str(index) + '】字段创建成功!')

  except Exception as e:
    return {"code": -1, "msg": "参数错误!"}
    # raise ("参数错误!")
