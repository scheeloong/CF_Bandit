import numpy as np
import random
class LinUCBUserStruct:
	def __init__(self, featureDimension, lambda_, init="zero"):
		self.d = featureDimension
		self.A = lambda_*np.identity(n = self.d)
		self.b = np.zeros(self.d)
		self.AInv = np.linalg.inv(self.A)
		if (init=="random"):
			self.UserTheta = np.random.rand(self.d)
		else:
			self.UserTheta = np.zeros(self.d)

	def updateParameters(self, articlePicked_FeatureVector, click):
		self.A += np.outer(articlePicked_FeatureVector,articlePicked_FeatureVector)
		self.b += articlePicked_FeatureVector*click
		self.AInv = np.linalg.inv(self.A)
		self.UserTheta = np.dot(self.AInv, self.b)
		
	def getTheta(self):
		return self.UserTheta
	
	def getA(self):
		return self.A

	def getProb(self, alpha, article_FeatureVector):
		mean = np.dot(self.UserTheta,  article_FeatureVector)
		var = np.sqrt(np.dot(np.dot(article_FeatureVector, self.AInv),  article_FeatureVector))
		pta = mean# + alpha * var
		return pta
	def getProb_plot(self, alpha, article_FeatureVector):
		mean = np.dot(self.UserTheta,  article_FeatureVector)
		var = np.sqrt(np.dot(np.dot(article_FeatureVector, self.AInv),  article_FeatureVector))
		pta = mean + alpha * var
		return pta, mean, alpha * var
class Uniform_LinUCBAlgorithm(object):
	def __init__(self, dimension, alpha, lambda_, init="zero"):
		self.dimension = dimension
		self.alpha = alpha
		self.USER = LinUCBUserStruct(dimension, lambda_, init)

		self.CanEstimateUserPreference = False
		self.CanEstimateCoUserPreference = True 
		self.CanEstimateW = False
	def decide(self, pool_articles, userID):
		maxPTA = float('-inf')
		articlePicked = None

		for x in pool_articles:
			x_pta = self.USER.getProb(self.alpha, x.featureVector[:self.dimension])
			if maxPTA < x_pta:
				articlePicked = x
				maxPTA = x_pta
		return articlePicked
	def updateParameters(self, articlePicked, click, userID):
		self.USER.updateParameters(articlePicked.featureVector[:self.dimension], click)
	def getCoTheta(self, userID):
		return self.USER.UserTheta



#---------------LinUCB(fixed user order) algorithm---------------
class N_LinEgreedyAlgorithm:
	def __init__(self, dimension, alpha, lambda_, n, init="zero"):  # n is number of users
		self.time = 1
		self.users = []
		#algorithm have n users, each user has a user structure
		for i in range(n):
			self.users.append(LinUCBUserStruct(dimension, lambda_ , init)) 

		self.dimension = dimension
		self.alpha = alpha

		self.CanEstimateUserPreference = False
		self.CanEstimateCoUserPreference = True
		self.CanEstimateW = False
	def decide(self, pool_articles, userID):
		maxPTA = float('-inf')
		articlePicked = None

		for x in pool_articles:
			x_pta = self.users[userID].getProb(self.alpha, x.featureVector[:self.dimension])
			# pick article with highest Prob
			if maxPTA < x_pta:
				articlePicked = x
				maxPTA = x_pta

		epsilon = self.get_epsilon()
		if random.random() > epsilon:
			return articlePicked
		else:
			return random.choice(pool_articles) 

	def get_epsilon(self):
		return min(100/self.time, 1)

	def updateParameters(self, articlePicked, click, userID):
		self.time += 1
		self.users[userID].updateParameters(articlePicked.featureVector[:self.dimension], click)
		
	def getCoTheta(self, userID):
		return self.users[userID].UserTheta
