"""
Read the raw data in. Then save the data and corresponding image ID in two lista. Then we can do feature selection and store the selected feature back.

Zhewei @ 9/25/2015

"""

import gzip, os
import pickle as Pickle
import numpy
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2, f_classif

TimeFrame = 130

class _EachSubject:
    # each subject is a element of a list
    def __init__(self, SubjectID, Sex, DX_Group, imageID):
        self.Sex = Sex
        self.DX_Group = DX_Group
        self.SubjectID = SubjectID
        # baseline is a dict, imageID:data
        self.baseline = {imageID:list()}
        # otherdata after baseline is also a dict, imageID:data
        self.other = {}

class _VTK_Subject:
    # for VTK class HM01
    def __init__(self, imageID, data, DX_Group):
        self.DX_Group = DX_Group;
        self.Data = {imageID:data}

def data_to_list(validDataList):
    Label = list()
    Data = list()
    ID = list()
    for validData in validDataList:
        tmp_list = list(validData.baseline.keys())
        for key in tmp_list:
            try:
                if validData.baseline[str(key)].any():
                    Label.append(validData.DX_Group)
                    Data.append(validData.baseline[str(key)])
                    ID.append(str(key))
                '''if str(key) == '228872':# test at here
                    print (validData.baseline[str(key)])'''
            except AttributeError:
                pass
        if validData.other != {}:
            tmp_list = list(validData.other.keys())
            for other_key in tmp_list:
                try:
                    if validData.other[str(other_key)].any():
                        Label.append(validData.DX_Group)
                        Data.append(validData.other[str(other_key)])
                        ID.append(str(other_key))
                except AttributeError:
                    pass
    return Label, Data, ID


def ReNewData(validDataList, Data_New, ID):
    no = 0
    for validData in validDataList:
        tmp_list = list(validData.baseline.keys())
        for key in tmp_list:
            try:
                if validData.baseline[str(key)].any():
                    position = ID.index(str(key))
                    dataNew = Data_new[TimeFrame*position:TimeFrame*(position+1),:]
                    validData.baseline[str(key)] = dataNew
                    no += 1
                if str(key) == '228872':# test at here
                    print (validData.baseline[str(key)])
                    print (validData.baseline[str(key)].shape)
            except AttributeError:
                pass
        if validData.other != {}:
            tmp_list = list(validData.other.keys())
            for other_key in tmp_list:
                try:
                    if validData.other[str(other_key)].any():
                        position = ID.index(str(other_key))
                        dataNew = Data_new[TimeFrame*position:TimeFrame*(position+1),:]
                        validData.other[str(other_key)] = dataNew
                        no += 1
                except AttributeError:
                    pass
    print (no)
    return validDataList

def stackData(Data_list):
    Data = numpy.zeros([1,1])
    for data_no, data in enumerate(Data_list):
        if data_no == 0:
            # Data = difference_of_data(data)
            Data = data
        else:
            # Data = numpy.hstack((Data, difference_of_data(data)))
            Data = numpy.hstack((Data, data))
    return Data.transpose()

def expandLabel_for_origin(Label_list):
    Label = list()
    for label in Label_list:
        Label += [label]*(TimeFrame)
    return Label

def expandLabel_for_residual(Label_list):
    Label = list()
    for label in Label_list:
        Label += [label]*(TimeFrame-1)
    return Label

def difference_of_data(dataList):
    timeframe = dataList[0].shape[1]
    print (timeframe)
    new_list = list()
    for data in dataList:
        tmp_data = numpy.zeros([1,1])
        for i in range(1, timeframe):
            if i == 1:
                tmp_data = data[:,i]-data[:,i-1]
            else:
                tmp_data = numpy.vstack((tmp_data, data[:,i]-data[:,i-1]))
        new_list.append(tmp_data.transpose())
    return new_list

def Normalize_Each_subject_as_One(dataList):
    for data in dataList:
        featureNo = data.shape[0]
        for i in range(featureNo):
            data[i,:] = data[i,:]/numpy.linalg.norm(data[i,:])

    print(dataList[0][0,:])
    return dataList


def Normlize_Each_subject_as_Zero_One(dataList):
    print (len(dataList))
    for data in dataList:
        featureNo = data.shape[0]
        for i in range(featureNo):
            max_value = numpy.amax(data[i,:])
            min_value = numpy.amin(data[i,:])
            data[i,:] = (data[i,:]-min_value)/(max_value-min_value)
    print(dataList[0][0,:])

    return dataList
        
        

os.chdir("/home/medialab/Zhewei/data/data_from_MATLAB/")
Raw_data = gzip.open('Subjects_180_ADNC.pickle.gz', 'rb')
Subjects_data = Pickle.load(Raw_data)
Label, Data, ID = data_to_list(Subjects_data)

# Now Data is a list of array [featureNo, timestep]. We need to stack the data
# print (len(Label))
# print (len(Data))
# print (Data[0].shape)

# If we use residual
Data = difference_of_data(Data)# Now Data is a list of array [featureNo, timestep-1].
# Now Lable is for each subject. We need to expand to each time frame
# Label_New = expandLabel_for_origin(Label)
Label_New = expandLabel_for_residual(Label)
# print (len(Label))
print (len(Label_New))

# Normalize the data
# Data = Normalize_Each_subject_as_One(Data)
Data = Normlize_Each_subject_as_Zero_One(Data)
print(Data[0].shape)
Data = stackData(Data)
# print (Data.shape)
print (Data[0:130,0])



Data_new = SelectKBest(chi2, k=120).fit_transform(Data, Label_New)
# print (Data_new[0:130,:])
# print (Data_new.shape)

# Now save it back. Travel the data structure, and feed the data back.
# print (ID)
NewSubjectsData = ReNewData(Subjects_data, Data_new, ID)   

"""for label_no, label in enumerate(Label):
    data = Data_new[TimeFrame*label_no:TimeFrame*(label_no+1),:]
    subject = _VTK_Subject(ID[label_no], data, label)
    VTK_DataList.append(subject)

with gzip.open('VTK_Subjects_180_difference.pickle.gz', 'wb') as output_file:
        Pickle.dump([Data_new, Label, ID], output_file, protocol=2)"""

with gzip.open('Feature_Selection_Normalize_as_zero_one_residual.pickle.gz', 'wb') as output_file:
    Pickle.dump(NewSubjectsData, output_file)


print('Done!')
    
    



