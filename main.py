from flask import Flask, request, render_template
from base_class.base_func import list_tables_func, list_fields_func, update_data_func
import os, urllib.parse, base64, hashlib
import configparser

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


def writeToINI(section, key, value):
  cfp = configparser.ConfigParser()
  if not os.path.exists('config.ini'):
    with open("config.ini", "w+") as f:
      cfp.write(f)

  cfp.read("config.ini")
  if not cfp.has_section(section):
    cfp.add_section(section)

  cfp.set(section, key, value)
  with open("config.ini", "w+") as f:
    cfp.write(f)


def readFromINI(section, key):
  cfp = configparser.ConfigParser()
  cfp.read("config.ini")
  value = cfp.get(section, key)
  return value


@app.route('/setup', methods=['GET', 'POST'])
def setup():
  if request.method == 'GET':

    userid = request.args.get("userid")
    baseid = request.args.get("baseid")
    urllib.parse.quote(userid, safe="")

    return render_template('setup.html', userid=userid, baseid=baseid)
  else:

    BASEID = request.form.get("baseid")
    USERID = urllib.parse.unquote(request.form.get("userid"))
    APP_TOKEN = request.form.get("app_token")
    PERSONAL_BASE_TOKEN = request.form.get("personal_base_token")

    if BASEID is None or BASEID == "":
      return '用户身份验证失败，请刷新页面重试'

    if USERID is None or USERID == "":
      return '用户身份验证失败，请刷新页面重试'

    if APP_TOKEN is None or APP_TOKEN == "":
      return 'app_token参数错误'

    if PERSONAL_BASE_TOKEN is None or PERSONAL_BASE_TOKEN == "":
      return 'personal_base_token参数错误'

    SECTION = BASEID + ":" + base64.b64encode(
        (BASEID + ":" + USERID).encode('utf-8')).decode()
    # print(SECTION, flush=True)

    writeToINI(SECTION, 'APP_TOKEN', APP_TOKEN)
    writeToINI(SECTION, 'PERSONAL_BASE_TOKEN', PERSONAL_BASE_TOKEN)
    return {'code': 200, 'data': 'APP_TOKEN 和 PERSONAL_BASE_TOKEN 保存成功!'}


@app.route('/', methods=['GET'])
def entry():
  return render_template('entry.html')


@app.route('/main', methods=['GET'])
def main():

  try:
    BASEID = request.args.get("baseid")
    USERID = request.args.get("userid")

    SECTION = BASEID + ":" + base64.b64encode(
        (BASEID + ":" + USERID).encode('utf-8')).decode()
    # print(SECTION, flush=True)
  except Exception as e:
    return '请在多维表格的扩展脚本中打开首页'

  try:
    APP_TOKEN = readFromINI(SECTION, 'APP_TOKEN')
    PERSONAL_BASE_TOKEN = readFromINI(SECTION, 'PERSONAL_BASE_TOKEN')

  except Exception as e:
    USERID = urllib.parse.quote(request.args.get("userid"), safe="")
    return render_template('setup.html', userid=USERID, baseid=BASEID)

  try:
    # data = list_tables_func(APP_TOKEN, PERSONAL_BASE_TOKEN)
    # return render_template('main.html',
    #                        tables_list=data.get("tables_list"),
    #                        fields_list=data.get("fields_list"),
    #                        section=SECTION,
    #                        base_token=PERSONAL_BASE_TOKEN)
    return render_template('main.html',
                           tables_list="",
                           fields_list="",
                           section=SECTION,
                           base_token=PERSONAL_BASE_TOKEN)
  except Exception as e:
    return '数据表列表获取错误！！！'


@app.route('/get_tables', methods=['POST'])
def get_tables():

  SECTION = request.args.get("section")

  try:
    APP_TOKEN = readFromINI(SECTION, 'APP_TOKEN')
  except Exception as e:
    return 'APP_TOKEN获取失败，请先进行初始化设置'

  try:
    PERSONAL_BASE_TOKEN = readFromINI(SECTION, 'PERSONAL_BASE_TOKEN')
  except Exception as e:
    return 'PERSONAL_BASE_TOKEN获取失败，请先进行初始化设置'

  try:
    result = list_tables_func(APP_TOKEN, PERSONAL_BASE_TOKEN)
    # print(result.get("tables_list"),flush=True)
    return {"code": 200, "data": result.get("tables_list")}
  except Exception as e:
    return '数据表列表获取错误！！！'


@app.route('/get_fields', methods=['POST'])
def get_fields():

  SECTION = request.args.get("section")

  try:
    APP_TOKEN = readFromINI(SECTION, 'APP_TOKEN')
  except Exception as e:
    return 'APP_TOKEN获取失败，请先进行初始化设置'

  try:
    PERSONAL_BASE_TOKEN = readFromINI(SECTION, 'PERSONAL_BASE_TOKEN')
  except Exception as e:
    return 'PERSONAL_BASE_TOKEN获取失败，请先进行初始化设置'

  TABLE_ID = request.form.get("table_id")

  try:
    result = list_fields_func(APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID)
    return {"code": 200, "data": result}
  except Exception as e:
    return '数据表字段获取错误！！！'


@app.route('/update_data', methods=['POST'])
def update_data():

  SECTION = request.args.get("section")

  try:
    APP_TOKEN = readFromINI(SECTION, 'APP_TOKEN')
  except Exception as e:
    return 'APP_TOKEN获取失败，请先进行初始化设置'

  try:
    PERSONAL_BASE_TOKEN = readFromINI(SECTION, 'PERSONAL_BASE_TOKEN')
  except Exception as e:
    return 'PERSONAL_BASE_TOKEN获取失败，请先进行初始化设置'

  TABLE_ID = request.form.get("table_id")
  FIELD_NAME = request.form.get("field_name")
  SEPARATOR = request.form.get("separator")

  try:
    result = update_data_func(APP_TOKEN, PERSONAL_BASE_TOKEN, TABLE_ID,
                              FIELD_NAME, SEPARATOR)
    return {"code": 200, "data": result}

  except Exception as e:
    return '数据分列失败！！！'


app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=True)
