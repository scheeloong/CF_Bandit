import sys
from conf import *     # it saves the address of data stored and where to save the data produced by algorithms
import argparse # For argument parsing
import time
import re             # regular expression library
from random import random, choice,shuffle     # for random strategy
from operator import itemgetter
import datetime
import numpy as np     
import sys
from scipy.sparse import csgraph
from scipy.spatial import distance
from YahooExp_util_functions import *


from CoLin import AsyCoLinUCBUserSharedStruct, AsyCoLinUCBAlgorithm, CoLinUCBUserSharedStruct
from GOBLin import GOBLinSharedStruct
from LinUCB import N_LinUCBAlgorithm#LinUCBUserStruct, Hybrid_LinUCBUserStruct
from factorLinUCB import FactorLinUCBAlgorithm
from CF_UCB import CFUCBAlgorithm
from CFEgreedy import CFEgreedyAlgorithm
from EgreedyContextual import EgreedyContextualStruct
from PTS import PTSAlgorithm
from UCBPMF import UCBPMFAlgorithm
from CLUB import CLUBAlgorithm
from COFIBA import COFIBAAlgorithm


from W_Alg import LearnWAlgorithm
from W_Alg_Gradient import LearnWAlgorithm_G
from W_Alg_L1_G import LearnWAlgorithm_l1_G
from W_Alg_L1 import LearnWAlgorithm_l1
from W_Alg_Gradient_UpdateA import LearnWAlgorithm_G_UpdateA, LearnWAlgorithm_G_WRegu_UpdateA
from W_Alg_L1_G_UpdateA import LearnWAlgorithm_l1_G_UpdateA

import warnings

# python YahooMain.py  --YahooDataFile ../../../MyResearch/datasets/R6/ --alg LearnWl2_UpdateA --userNum 160 --Sparsity 160 --diag Orgin
# structure to save data from random strategy as mentioned in LiHongs paper
class randomStruct:
    def __init__(self):
        self.learn_stats = articleAccess()
class Article():    
    def __init__(self, aid, FV=None):
        self.id = aid
        self.featureVector = FV
        self.contextFeatureVector = FV

if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    # regularly print stuff to see if everything is going alright.
    # this function is inside main so that it shares variables with main and I dont wanna have large number of function arguments
    def printWrite():
        randomLearnCTR = articles_random.learn_stats.updateCTR()
        recordedStats = [randomLearnCTR]
        for alg_name, alg in algorithms.items():
            algCTR = alg.learn_stats.updateCTR()
            recordedStats.append(algCTR)
            recordedStats.append(alg.learn_stats.accesses)
            recordedStats.append(alg.learn_stats.clicks)        
        # write to file
        save_to_file(fileNameWrite, recordedStats, tim) 
    def WriteStat():
        with open(fileNameWriteStatTP, 'a+') as f:
            for key, val in articleTruePositve.items():
                f.write(str(key) + ';'+str(val) + ',')
            f.write('\n')
        with open(fileNameWriteStatTN, 'a+') as f:
            for key, val in articleTrueNegative.items():
                f.write(str(key) + ';'+str(val) + ',')
            f.write('\n')
        with open(fileNameWriteStatFP, 'a+') as f:
            for key, val in articleFalsePositive.items():
                f.write(str(key) + ';'+str(val) + ',')
            f.write('\n')


    def calculateStat():
        if click:        
            for article in currentArticles:
                if article == article_chosen:
                    articleTruePositve[article_chosen] +=1
                else:
                    articleTrueNegative[article] +=1                
        else:
            for article in currentArticles:
                if article == article_chosen:
                    articleFalsePositive[article_chosen] +=1

    parser = argparse.ArgumentParser(description = '')
    parser.add_argument('--YahooDataFile', dest="Yahoo_save_address", help="input the adress for Yahoo data")
    parser.add_argument('--alg', dest='alg', help='Select a specific algorithm, could be CoLin, GOBLin, LinUCB, HybridLinUCB, CFUCB, CFEgreedy, SGDEgreedy, PTS.')

    parser.add_argument('--showheatmap', action='store_true',
                    help='Show heatmap of relation matrix.') 
    parser.add_argument('--userNum', dest = 'userNum', help = 'Set the userNum, can be 20, 40, 80, 160')

    parser.add_argument('--Sparsity', dest = 'SparsityLevel', help ='Set the SparsityLevel by choosing the top M most connected users, should be smaller than userNum, when equal to userNum, we are using a full connected graph')
    parser.add_argument('--diag', dest="DiagType", help="Specify the setting of diagional setting, can be set as 'Orgin' or 'Opt' ") 

    parser.add_argument('--particle_num', 
                        help='Particle number for PTS.')
    parser.add_argument('--dimension', 
                        help='Feature dimension used for estimation.')
    # Load previous running status.
    parser.add_argument('--load', 
                        help='Load previous running status.')

    args = parser.parse_args()

    algName = str(args.alg)
    clusterNum = int(args.userNum)
    SparsityLevel = int(args.SparsityLevel)
    yahooData_address = str(args.Yahoo_save_address)
    DiagType = str(args.DiagType)
    
    timeRun = datetime.datetime.now().strftime('_%m_%d_%H_%M')     # the current data time
    dataDays = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
    fileSig = str(algName)+str(clusterNum)+ 'SP'+ str(SparsityLevel)+algName
    batchSize = 2000
    statBatchSize = 200000                            # size of one batch
    
    d = 5             # feature dimension
    context_dimension = d
    latent_dimension = 2
    alpha = 0.3     # control how much to explore
    lambda_ = 0.2   # regularization used in matrix A
    epsilon = 0.3
    
    itemNum = 200000

    totalObservations = 0

    articleTruePositve = {}
    articleFalseNegative = {}

    articleTrueNegative = {}
    articleFalsePositive = {}

    fileNameWriteCluster = os.path.join(Kmeansdata_address, '10kmeans_model'+str(clusterNum)+ '.dat')
    userFeatureVectors = getClusters(fileNameWriteCluster)    
    userNum = clusterNum
    if DiagType == 'Orgin':
        W = initializeW(userFeatureVectors, SparsityLevel)
    elif DiagType == 'Opt':
        W = initializeW_opt(userFeatureVectors, SparsityLevel)   # Generate user relation matrix
    GW = initializeGW(W , epsilon)
     
    articles_random = randomStruct()
    algorithms = {}
    runCoLinUCB = runGOBLin = runLinUCB = run_M_LinUCB = run_Uniform_LinUCB= run_CFUCB = run_CFEgreedy = run_SGDEgreedy = run_PTS = False
    LearnWl2 = LearnWl2_UpdateA = LearnWl1 = LearnWl1_UpdateA = LearnW_WRegu_UpdateA = False

    tsave = 60*60*47 # Time interval for saving model.
    #tsave = 6
    tstart = time.time()

    if args.load:
        fileSig, timeRun = args.load.split('__')
        fileSig = fileSig+'_'
        timeRun = '_'+timeRun
        print (fileSig, timeRun)
        with open(args.load +'.model', 'r') as fin:
            obj = pickle.load(fin)
        with open(args.load +'.txt', 'r') as fin:
            finished_day = int(fin.readline().strip().split()[1])
            finished_line = int(fin.readline().strip().split()[1])
            print (finished_day, finished_line)

    if args.alg:
        if args.alg == 'CoLinUCB':
            runCoLinUCB = True
            if args.load:
                algorithms['CoLin'] = obj
            else:
                algorithms['CoLin'] = AsyCoLinUCBAlgorithm(dimension=context_dimension, alpha = alpha, lambda_ = lambda_, n = userNum, W = W)
        elif args.alg == 'LearnWl2':
            runLearnWl2 = True
            if args.load:
                algorithms['LearnWl2'] = obj
            else:
                algorithms['LearnWl2'] = LearnWAlgorithm_G(dimension = context_dimension, alpha = alpha, lambda_ = lambda_,  n = userNum, W = W, windowSize = userNum*100, RankoneInverse=False)
        elif args.alg == 'LearnWl2_UpdateA':
            LearnWl2_UpdateA = True
            if args.load:
                algorithms['LearnWl2_UpdateA'] = obj
            else:
                algorithms['LearnWl2_UpdateA'] = LearnWAlgorithm_G_UpdateA(dimension = context_dimension, alpha = alpha, lambda_ = lambda_,  n = userNum, W = W, windowSize = userNum*100, RankoneInverse=False)
        elif args.alg == 'LearnW_WRegu_UpdateA':
            LearnW_WRegu_UpdateA = True
            if args.load:
                algorithms['LearnW_WRegu_UpdateA'] = obj
            else:
                algorithms['LearnW_WRegu_UpdateA'] = LearnWAlgorithm_G_WRegu_UpdateA(dimension = context_dimension, alpha = alpha, lambda_ = lambda_,  n = userNum, W = W, windowSize = userNum*100, RankoneInverse=False)
        elif args.alg == 'LearnWl1':
            LearnWl1 = True
            if args.load:
                algorithms['LearnWl1'] = obj
            else:
                algorithms['LearnWl1'] = LearnWAlgorithm_l1_G(dimension = context_dimension, alpha = alpha, lambda_ = lambda_,  n = userNum, W = W, windowSize = userNum*100, RankoneInverse=True)

        elif args.alg == 'LearnWl1_UpdateA':
            LearnWl1_UpdateA = True
            if args.load:
                algorithms['LearnWl1_UpdateA'] = obj
            else:
                algorithms['LearnWl1_UpdateA'] =  LearnWAlgorithm_l1_G_UpdateA(dimension = context_dimension, alpha = alpha, lambda_ = lambda_,  n = userNum, W = W, windowSize = userNum*100, RankoneInverse=True)
        elif args.alg == 'GOBLin':
            runGOBLin = True
        elif args.alg == 'LinUCB':
            runLinUCB = True
            if args.load:
                algorithms['LinUCB'] = obj
            else:
                algorithms['LinUCB'] = N_LinUCBAlgorithm(dimension = context_dimension, alpha = alpha, lambda_ = lambda_, n = clusterNum)
        elif args.alg =='M_LinUCB':
            run_M_LinUCB = True
        elif args.alg == 'Uniform_LinUCB':
            run_Uniform_LinUCB = True
        elif args.alg == 'CFUCB':
            run_CFUCB = True
            if not args.dimension:
                dimension = 5
            else:
                dimension = int(args.dimension)
            if args.load:
                algorithms['CFUCB'] = obj
            else:
                algorithms['CFUCB'] = CFUCBAlgorithm(context_dimension = context_dimension, latent_dimension = dimension, alpha = 0.2, alpha2 = 0.1, lambda_ = lambda_, n = clusterNum, itemNum=itemNum, init='random', window_size = 3)
        elif args.alg == 'factorLinUCB':
            run_factorLinUCB = True
            if not args.dimension:
                dimension = 5
            else:
                dimension = int(args.dimension)
            if args.load:
                algorithms['FactorLinUCBAlgorithm'] = obj
            else:
                algorithms['FactorLinUCBAlgorithm'] = FactorLinUCBAlgorithm(context_dimension = context_dimension, latent_dimension = dimension, alpha = 0.2, alpha2 = 0.1, lambda_ = lambda_, n = clusterNum, itemNum=itemNum, W = W, init='random', window_size = 3)    
        elif args.alg == 'CLUB':
            run_CLUB = True
            if args.load:
                algorithms['CLUB'] = obj
            else:
                algorithms['CLUB'] = CLUBAlgorithm(dimension =context_dimension,alpha = alpha, lambda_ = lambda_, n = OriginaluserNum, alpha_2 = alpha_2, cluster_init = 'Erdos-Renyi') 
        elif args.alg == 'COFIBA':
            run_COFIBA = True
            if args.load:
                algorithms['COFIBA'] = obj
            else:
                algorithms['COFIBA'] = COFIBAAlgorithm(dimension =context_dimension,alpha = alpha,  alpha_2 = alpha_2, lambda_ = lambda_, n = OriginaluserNum, itemNum = itemNum,cluster_init = 'Erdos-Renyi') 

        elif args.alg == 'CFEgreedy':
            run_CFEgreedy = True
            if not args.dimension:
                dimension = 5
            else:
                dimension = int(args.dimension)
            if args.load:
                algorithms['CFEgreedy'] = obj
            else:
                algorithms['CFEgreedy'] = CFEgreedyAlgorithm(context_dimension = context_dimension, latent_dimension = dimension, alpha = 200, lambda_ = lambda_, n = clusterNum, itemNum=itemNum, init='random')
        elif args.alg == 'SGDEgreedy':
            run_SGDEgreedy = True
            if not args.dimension:
                dimension = 5
            else:
                dimension = int(args.dimension)
            if args.load:
                algorithms['SGDEgreedy'] = obj
            else:
                algorithms['SGDEgreedy'] = EgreedyContextualStruct(epsilon_init=200, userNum=clusterNum, itemNum=itemNum, k=dimension, feature_dim = context_dimension, lambda_ = lambda_, init='random', learning_rate='constant')
        elif args.alg == 'PTS':
            run_PTS = True
            if not args.particle_num:
                particle_num = 10
            else:
                particle_num = int(args.particle_num)
            if not args.dimension:
                dimension = 5
            else:
                dimension = int(args.dimension)
            if args.load:
                algorithms['PTS'] = obj
            else:
                algorithms['PTS'] = PTSAlgorithm(particle_num = particle_num, dimension = dimension, n = clusterNum, itemNum=itemNum, sigma = np.sqrt(.5), sigmaU = 1, sigmaV = 1)
        elif args.alg == 'UCBPMF':
            run_UCBPMF = True
            if not args.dimension:
                dimension = 5
            else:
                dimension = int(args.dimension)
            if args.load:
                algorithms['UCBPMF'] = obj
            else:
                algorithms['UCBPMF'] = UCBPMFAlgorithm(dimension = dimension, n = clusterNum, itemNum=itemNum, sigma = np.sqrt(.5), sigmaU = 1, sigmaV = 1, alpha = 0.1)

        elif args.alg == 'ALL':
            runCoLinUCB = runGOBLin = runLinUCB = run_M_LinUCB = run_Uniform_LinUCB=True
    else:
        args.alg = 'Random'


    for alg_name, alg in algorithms.items():
        if not args.load:
            alg.learn_stats = articleAccess()
  
    for dataDay in dataDays:
        if args.load:
            if int(dataDay)< finished_day:
                continue
        fileName = yahooData_address + "/ydata-fp-td-clicks-v1_0.200905" + dataDay    +'.'+ str(userNum) +'.userID'
        fileNameWrite = os.path.join(Yahoo_save_address, fileSig + dataDay + timeRun + '.csv')

        fileNameWriteStatTP = os.path.join(Yahoo_save_address, 'Stat_TP'+ fileSig + dataDay + timeRun + '.csv')
        fileNameWriteStatTN = os.path.join(Yahoo_save_address, 'Stat_TN'+ fileSig + dataDay + timeRun + '.csv')
        fileNameWriteStatFP = os.path.join(Yahoo_save_address, 'Stat_FP'+ fileSig + dataDay + timeRun + '.csv')

        # put some new data in file for readability
        with open(fileNameWrite, 'a+') as f:
            f.write('\nNewRunat  ' + datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S'))
            f.write('\n,Time,RandomCTR;'+ str(algName) + 'CTR;' + 'accesses;'+ 'clicks;' + '' +'\n')

        print (fileName, fileNameWrite)
        with open(fileName, 'r') as f:
            # reading file line ie observations running one at a time
            for i, line in enumerate(f, 1):
                if args.load:
                    if i< finished_line:
                        continue
                totalObservations +=1

                tim, article_chosen, click, currentUserID, pool_articles = parseLine_ID(line)
                #currentUser_featureVector = user_features[:-1]
                #currentUserID = getIDAssignment(np.asarray(currentUser_featureVector), userFeatureVectors)                
                #-----------------------------Pick an article (CoLinUCB, LinUCB, Random)-------------------------
                articlePool = []    
                currentArticles = []            
                for article in pool_articles:
                    article_id = int(article[0])
                    article_featureVector =np.asarray(article[1:6])
                    articlePool.append(Article(article_id, article_featureVector))
                    currentArticles.append(article_id)  
                shuffle(articlePool)
                for article in currentArticles:
                    if article not in articleTruePositve:
                        articleTruePositve[article] = 0
                        articleTrueNegative[article] = 0
                        articleFalsePositive[article] = 0
                        articleFalseNegative[article] = 0
                # article picked by random strategy
                articles_random.learn_stats.addrecord(click)
                for alg_name, alg in algorithms.items():
                    pickedArticle = alg.decide(articlePool, currentUserID)
                    # reward = getReward(userID, pickedArticle) 
                    if (pickedArticle.id == article_chosen):
                        alg.learn_stats.addrecord(click)
                        alg.updateParameters(pickedArticle, click, currentUserID)
                        calculateStat()
	                

                # if the batch has ended
                if totalObservations%batchSize==0:
                    printWrite()
                    tend = time.time()
                    '''
                    if tend-tstart>tsave:
                        model_name = 'Yahoo_'+str(clusterNum)+'_'+alg_name+'_'+dataDay+'_' + timeRun                    
                        model_dump(alg, model_name, line, dataDay)
                        tstart = tend
                    '''
                if totalObservations%statBatchSize==0:
                    WriteStat()
            #print stuff to screen and save parameters to file when the Yahoo! dataset file ends
            printWrite()
            WriteStat()
        for alg_name, alg in algorithms.items():
            model_name = 'Yahoo_'+str(clusterNum)+'_'+alg_name+'_'+dataDay+'_' + timeRun                    
            model_dump(alg, model_name, line, dataDay)
            tstart = tend
        # sys.exit()  
