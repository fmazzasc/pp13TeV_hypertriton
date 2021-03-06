import utils, mass_fit, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from hipe4ml.model_handler import ModelHandler
from hipe4ml.tree_handler import TreeHandler
from hipe4ml.analysis_utils import score_from_efficiency_array


def save_data_with_scores(tree_handler, filename):
    print('Saving file: ' + filename + '\n')
    tree_handler.write_df_to_parquet_files(filename)      #to_parquet, get_handler_from_large_data, get_data_frame

def load_data_with_scores(filename):
    return pd.read_parquet(filename)

def save_eff_scores(eff_array, scores, test):
    
    if test:
        eff_name = '../data/eff_array_Test.csv'
        scores_name = '../data/scores_Test.csv'
    
    else: 
        eff_name = '../data/eff_array.csv'
        scores_name = '../data/scores.csv'

    with open(eff_name,'w') as f:
        for val in eff_array:
            f.write(str(np.round(val,4)))
            f.write('\n')
    f.close()

    with open(scores_name,'w') as f:
        for val in scores:
            f.write(str(np.round(val,4)))
            f.write('\n')
    f.close()

def load_eff_scores():
    with open('../data/eff_array.csv') as f:
        eff_array = np.array(f.read().splitlines()).astype(np.float)
    f.close()

    with open('../data/scores.csv') as f:
        scores = np.array(f.read().splitlines()).astype(np.float)
    f.close()

    return eff_array, scores

def train_model(optimize_bayes = False, test = False):
    
    if test:
        mc_signal = TreeHandler()
        mc_signal.get_handler_from_large_file(file_name = '../data/SignalTable_pp13TeV_mtexp_Test.root',tree_name= "SignalTable",
                                                preselection='rej_accept > 0 and pt > 1.5')
        print('MC signal loaded\n')

        background_ls = TreeHandler()
        background_ls.get_handler_from_large_file(file_name = '../data/DataTable_pp_LS_Test.root',tree_name= "DataTable",
                                                    preselection='centrality < 0.17 and pt > 1.5')
        background_ls.shuffle_data_frame(size = min(background_ls.get_n_cand(), mc_signal.get_n_cand() * 4))
        print('Background LS loaded\n')

    else:
        mc_signal = TreeHandler()
        mc_signal.get_handler_from_large_file(file_name = '../data/SignalTable_pp13TeV_mtexp.root',tree_name= "SignalTable",
                                                preselection='rej_accept > 0 and pt > 1.5')
        print('MC signal loaded\n')

        background_ls = TreeHandler()
        background_ls.get_handler_from_large_file(file_name = '../data/DataTable_pp_LS.root',tree_name= "DataTable",
                                                    preselection='centrality < 0.17 and pt > 1.5')
        background_ls.shuffle_data_frame(size = min(background_ls.get_n_cand(), mc_signal.get_n_cand() * 4))
        print('Background LS loaded\n')

    '''
    for var in ['dca_pr', 'dca_pi', 'dca_de']:
        plt.figure()
        plt.hist(data[var],bins=100)
        plt.title(var + ' - Data', fontsize=15)
        plt.xlabel(var, fontsize=12)
        plt.ylabel('Count',fontsize=12)
        plt.savefig("../images/data_" + var + ".png",dpi = 300, facecolor = 'white')
        plt.show()
        plt.close()
        
        plt.figure()
        plt.hist(mc_signal[var],bins=100)
        plt.title(var + ' - MC', fontsize=15)
        plt.xlabel(var, fontsize=12)
        plt.ylabel('Count',fontsize=12)
        plt.savefig("../images/MC_" + var + ".png",dpi = 300, facecolor = 'white')
        plt.show()
        plt.close()
    '''

    training_variables = ["pt", "cos_pa" , "tpc_ncls_de" , "tpc_ncls_pr" , "tpc_ncls_pi", "tpc_nsig_de", "tpc_nsig_pr",
                            "tpc_nsig_pi", "dca_de_pr", "dca_de_pi", "dca_pr_pi", "dca_de_sv", "dca_pr_sv", "dca_pi_sv", "chi2"] #,'dca_pr', 'dca_pi', 'dca_de'
    min_eff = 0.5
    max_eff = 0.9
    step = 0.01
    eff_array = np.arange(min_eff, max_eff, step)

    train_test_data, y_pred_test, model_hdl = utils.train_xgboost_model(mc_signal, background_ls, training_variables, optimize_bayes = optimize_bayes)
    
    model_path = "../model"
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    
    if test:
        model_hdl.dump_model_handler(model_path + '/model_hdl_Test')
    else:
        model_hdl.dump_model_handler(model_path + '/model_hdl')


    scores = score_from_efficiency_array(train_test_data[3],y_pred_test,np.arange(min_eff,max_eff,step))

    del background_ls

    if test:
        data = TreeHandler()
        data.get_handler_from_large_file(file_name = '../data/DataTable_pp_Test.root',tree_name= "DataTable",
                                            preselection='centrality < 0.17 and pt > 1.5', model_handler = model_hdl)
        print('Data loaded\n')
        background_ls = TreeHandler()
        background_ls.get_handler_from_large_file(file_name = '../data/DataTable_pp_LS_Test.root',tree_name= "DataTable",
                                            preselection='centrality < 0.17 and pt > 1.5', model_handler = model_hdl)
        print('Background loaded\n')
    else:
        data = TreeHandler()
        data.get_handler_from_large_file(file_name = '../data/DataTable_pp.root',tree_name= "DataTable",
                                            preselection='centrality < 0.17 and pt > 1.5', model_handler = model_hdl)
        print('Data loaded\n')
        background_ls = TreeHandler()
        background_ls.get_handler_from_large_file(file_name = '../data/DataTable_pp_LS.root',tree_name= "DataTable",
                                            preselection='centrality < 0.17 and pt > 1.5', model_handler = model_hdl)
        print('Background loaded\n')

    #background_ls.apply_model_handler(model_hdl)
    #data.apply_model_handler(model_hdl)

    print(background_ls)

    if test:
        save_data_with_scores(background_ls, '../data/bckg_ls_scores_Test')
        save_data_with_scores(data, '../data/data_scores_Test')
    else:
        save_data_with_scores(background_ls, '../data/bckg_ls_scores')
        save_data_with_scores(data, '../data/data_scores')

    save_eff_scores(eff_array, scores, test)





