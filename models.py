import time

from scipy.linalg import solve
from sklearn.base import BaseEstimator
from sklearn.preprocessing import LabelBinarizer
from tqdm import tqdm

from kernels import *
from utils import augment_dataset, HOGExtractor


class KernelRidgeRegressor(BaseEstimator):

    def __init__(self, C=1.0, kernel='rbf', gamma=10):
        self.C = C
        self.kernel = kernel
        self.gamma = gamma
        self.K = None
        self.alpha = None

    def fit(self, X, y):
        # initialize kernel
        self.K = kernels[self.kernel](X, self.gamma)
        print("Start computing kernel similarity matrix...")
        start = time.time()
        K = self.K.similarity_matrix()
        end = time.time()
        print(f"Kernel similarity matrix computed in {end - start:.2f} seconds")

        # compute first term
        diag = np.zeros_like(K)
        np.fill_diagonal(diag, self.C * len(X))
        K += diag
        self.alpha = solve(K, y, assume_a='pos')
        return self

    def predict(self, X):
        print("Predicting...")
        preds = []
        for x in tqdm(X):
            similarity = self.K.similarity(x)
            preds.append(np.dot(self.alpha, similarity))
        return np.array(preds)


class KernelRidgeClassifier(BaseEstimator):

    def __init__(self, C=1.0, kernel='rbf', gamma=10):
        self.C = C
        self.kernel = kernel
        self.gamma = gamma
        self.K = None
        self.alpha = None

    def fit(self, X, y):
        # map labels in {-1, 1}
        Y = LabelBinarizer(pos_label=1, neg_label=-1).fit_transform(y)
        # initialize kernel
        self.K = kernels[self.kernel](X, self.gamma)
        print("Start computing kernel similarity matrix...")
        start = time.time()
        K = self.K.similarity_matrix()
        end = time.time()
        print(f"Kernel similarity matrix computed in {end - start:.2f} seconds")

        # compute first term
        diag = np.zeros_like(K)
        np.fill_diagonal(diag, self.C * len(X))
        K += diag
        # compute coefficients for each class, one-vs-all
        self.alpha = []
        for c in tqdm(sorted(set(y))):
            self.alpha.append(solve(K, Y[:, c], assume_a='pos'))
        self.alpha = np.array(self.alpha)
        return self

    def predict(self, X):
        print("Predicting...")
        preds = []
        for x in tqdm(X):
            similarity = self.K.similarity(x)
            preds.append(np.argmax([np.dot(alpha, similarity) for alpha in self.alpha]))
        return np.array(preds)


class AugmentedHogsKernelRidgeClassifier(BaseEstimator):

    def __init__(self, C=1.0, kernel='rbf', gamma=10, flip_ratio=0.2, rot_replicas=1, rot_ratio=0.2, rot_angle=20):
        self.C = C
        self.kernel = kernel
        self.gamma = gamma
        self.flip_ratio = flip_ratio
        self.rot_replicas = rot_replicas
        self.rot_ratio = rot_ratio
        self.rot_angle = rot_angle
        self.hog_extractor = HOGExtractor()
        self.K = None
        self.alpha = None

    def fit(self, X, y):
        # augment dataset
        X, y = augment_dataset(X, y, self.flip_ratio, self.rot_replicas, self.rot_ratio, self.rot_angle)
        # get HOGs
        X = self.hog_extractor.transform(X)
        # map labels in {-1, 1}
        Y = LabelBinarizer(pos_label=1, neg_label=-1).fit_transform(y)
        # initialize kernel
        self.K = kernels[self.kernel](X, self.gamma)
        print("Start computing kernel similarity matrix...")
        start = time.time()
        K = self.K.similarity_matrix()
        end = time.time()
        print(f"Kernel similarity matrix computed in {end - start:.2f} seconds")

        # compute first term
        diag = np.zeros_like(K)
        np.fill_diagonal(diag, self.C * len(X))
        K += diag
        # compute coefficients for each class, one-vs-all
        self.alpha = []
        for c in tqdm(sorted(set(y))):
            self.alpha.append(solve(K, Y[:, c], assume_a='pos'))
        self.alpha = np.array(self.alpha)
        return self

    def predict(self, X):
        print("Predicting...")
        # get hogs
        X = self.hog_extractor.transform(X)
        preds = []
        for x in tqdm(X):
            similarity = self.K.similarity(x)
            preds.append(np.argmax([np.dot(alpha, similarity) for alpha in self.alpha]))
        return np.array(preds)
