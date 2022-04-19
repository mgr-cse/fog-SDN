from doctest import testmod
from unittest import result
import numpy as np
import pandas as pd

#@title number of hosts
# choose number of hosts to generate combined_train.csv
numHosts = 10 #@param {type:"integer"}
models = ['dtree_depth5', 'dtree_depth10', 'random_forest50_depth10', 'svc_linear','lin_logloss_sgd_stop5', 'lin_logloss_sgd_stop10', 'lin_logloss_sgd_stop15', 'lin_logloss_sgd_nostop']

sdn_fog_folder = './'

def ParseCSV(hostNum:int, runId:int, model_descriptor:str):
  folderpath = sdn_fog_folder + '/flow-data/' + str(hostNum) + '/'
  send_params_path = folderpath + 'pcaps/' + str(runId) + '/sendParams.csv'
  topo_path = folderpath + 'pcaps/' + str(runId) + '/topo.csv'

  # classified pox log
  flow_log_path = sdn_fog_folder + 'test-data/' + model_descriptor + '/' +str(hostNum) + '/test' + str(runId) + '.txt'

  topo = dict()
  with open(topo_path, 'r') as f:
    lines = f.readlines()[1:]
    for line in lines:
      s = line.split(',')
      topo[s[0]] = s[1][:-3]

  # print(topo)

  flow_labels = dict()
  ports = list()

  with open(send_params_path, 'r') as f:
    lines = f.readlines()[1:]
    for line in lines:
      comps = line.split(',')
      nw_src = topo[comps[0]]
      nw_dst = comps[1]

      flow_labels[hash(''.join([nw_src, nw_dst]))] = 1 if "Telnet" in comps[-1] else 0
      flow_labels[hash(''.join([nw_dst, nw_src]))] = flow_labels[hash(''.join([nw_src, nw_dst]))]
      ports.append(int(comps[2]))

  # print(flow_labels)
  # print(ports)

  data = pd.read_csv(flow_log_path)

  labels = list()
  for i in range(len(data)):
    flow = data.iloc[i, :]
    nw_src = flow['source.IP']
    nw_dst = flow['dest.IP']
    tp_src = flow['source.port']
    tp_dst = flow['dest.port']
    key = hash(''.join([nw_src, nw_dst]))
    if (tp_src in ports) or (tp_dst in ports):
      labels.append(flow_labels[key])
    else:
      labels.append(0)
  data['labels'] = pd.Series(labels)

  # print(data.head())
  #data.to_csv(folderpath + "/labeled_flow.csv", index= False)
  return data

# joined the parsed data
def combined_data(numHosts:int, model_descriptor:str):
    joinedData = ParseCSV(numHosts, 6, model_descriptor)
    for i in range(7, 11, 1):
      joinedData = pd.concat([joinedData, ParseCSV(numHosts, i, model_descriptor)], ignore_index=True)

    joinedData.to_csv(sdn_fog_folder + 'test-data/combined_train_' + model_descriptor + '_'+ str(numHosts) + ".csv", index= False)

cols = ['source.IP','dest.IP','source.port','dest.port','fwd.total_packets','fwd.total_bytes','bwd.total_packets','bwd.total_bytes','duration','labels']
def formatData(numHosts:int, model_descriptor:str):
    combined_data(numHosts, model_descriptor)
    filename = "combined_train_" + model_descriptor + '_' + str(numHosts) + ".csv"
    train = pd.read_csv('./test-data/' + filename, usecols= cols)

    train['source.IP'] = train['source.IP'].astype('str')
    train['dest.IP'] = train['dest.IP'].astype('str')
    train['source.port'] = train['source.port'].astype('int64')
    train['dest.port'] = train['dest.port'].astype('int64')
    for col in cols[4:9]:
        train[col] = train[col].astype('float64')
    train['labels'] = train['labels'].astype('int64')

    return train

from sklearn.base import BaseEstimator, TransformerMixin

class IPTransformer(BaseEstimator, TransformerMixin):
  def __init__(self):
    print("Parse both source & dest IP fields to 4 int fields, drop original IP fields")

  def parseIP(self, ip_list):
    ip1 = []
    ip2 = []
    ip3 = []
    ip4 = []
    for ip in ip_list:
      s = ip.split('.')
      # print(s)
      ip1.append(int(s[0]))
      ip2.append(int(s[1]))
      ip3.append(int(s[2]))
      ip4.append(int(s[3]))
    
    return ip1, ip2, ip3, ip4
  
  def fit(self, X, y=None):
    return self

  def transform(self, X):
    df = pd.DataFrame(columns= cols)
    if isinstance(X, pd.Series):
      # print("series input")
      df = df.append(X, ignore_index= True)
    else:
      # print("dataframe input")
      df = pd.concat([df, X], ignore_index= True)

    nw_src_list = df['source.IP']
    nw_dst_list = df['dest.IP']
    src_ip_parsed = self.parseIP(nw_src_list)
    dst_ip_parsed = self.parseIP(nw_dst_list)

    df = df.drop(['source.IP', 'dest.IP'], axis= 1)

    for i in range(4):
      df['source.IP.'+ str(i+1)] = pd.Series(np.array(src_ip_parsed[i]))
      df['dest.IP.'+ str(i+1)] = pd.Series(np.array(dst_ip_parsed[i]))
    
    
    return df

import pickle

def testModel(numHosts:int, model_descriptor:str):
    testData = formatData(numHosts, model_descriptor)
    tr = IPTransformer()
    tr.fit(testData)
    parsed_test = tr.transform(testData)
    parsed_test.head()

    y = [int(i) for i in parsed_test['labels']]
    X = parsed_test.drop(['labels'], axis= 1)

    model_file = sdn_fog_folder + 'model/' + str(numHosts) + '/' + model_descriptor + '.pth'
    model = pickle.load(open(model_file, 'rb'))
    result = model.score(X, y)
    print(model_descriptor + ' Accuracy ' + str(result))

for m in models:
    testModel(numHosts, m)