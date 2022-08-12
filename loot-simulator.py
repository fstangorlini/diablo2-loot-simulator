############################################################
# Author: Felipe Stangorlini
# Aug-2022
# Version 0.1
############################################################

#####################################
# Imports
#####################################
import concurrent.futures
from dataclasses import dataclass
import time
import matplotlib.pyplot as plt
import json
import time
import datetime
from collections import OrderedDict
import pandas as pd
import random

#####################################
# Classes
#####################################
@dataclass
class TreasureClass:
    
    monster:str
    kills:int
    loot:dict
    df:pd.DataFrame

    # Initializes
    def __init__(self, monster:str):
        file_treasureclassex = './res/TreasureClassEx.txt'
        self.df = pd.read_csv(file_treasureclassex, sep="\t")
        self.monster = monster
        self.loot = None

    # Gets loot from a single monster (treasure class) kill
    def __get_loot__(self, currentTreasureClass, loot_array=[]):
        df_row = self.df[self.df['Treasure Class']==currentTreasureClass]
        if df_row.size > 0: # Loot Group, go deeper
            # Populates probability array for random choices
            probability_array = []
            if not pd.isna(df_row['NoDrop'].values[0]):
                probability_array.append(('No Drop',df_row['NoDrop'].values[0]))
            g = []
            for i in range(1,11): g.append(('Item'+str(i),'Prob'+str(i)))
            for i in g:
                if not pd.isna(df_row[i[0]].values[0]):
                    probability_array.append((df_row[i[0]].values[0],df_row[i[1]].values[0]))
            population = []
            weigths = []
            for p in probability_array: population.append(p[0])
            for w in probability_array: weigths.append(int(w[1]))
            picks = int(abs(df_row['Picks'].values[0]))
            # Runs random choices
            random_loots = random.choices(population, weights=weigths, k=picks)
            for loot in random_loots:
                self.__get_loot__(loot, loot_array)
            return loot_array
        else:
            if(currentTreasureClass != 'No Drop'):
                loot_array.append(currentTreasureClass)
            return loot_array

    # Gets multiple loot from single monster - Simulates multiple kills
    def __get_multiple_loot__(self, kills:int=1):
        self.kills = kills
        loot_dict = {}
        for i in range(self.kills):
            loot = self.__get_loot__(self.monster)
            for l in loot:
                if l in loot_dict: loot_dict[l] +=1
                else: loot_dict[l] = 1
        return loot_dict

    # Checks if item is a rune
    def __isRune__(self, item:str):
        if item.startswith('r0') or item.startswith('r1') or item.startswith('r2') or item.startswith('r3'): return True
        else: return False

    # Gets only runes from loot dictionary
    def get_runes(self):
        return dict(filter(lambda elem: self.__isRune__(str(elem[0])) , self.loot.items()))

    # Simulate kills with __get_multiple_loot__ executed in threads with concurrent.futures.ProcessPoolExecutor()
    def simulate_kills(self, kills:int, threads:int=10):
        self.kills = kills*threads
        print('------------------------------------------------------------------------------------------------')
        print(f'Starting kill simulation for monster [{self.monster}] killing it {self.kills} times...')
        start = time.perf_counter()
        list_of_times = [self.kills for _ in range(threads)]
        loot_dict = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            results = executor.map(treasureClass.__get_multiple_loot__, list_of_times)
            for result in results:
                loot_dict.update(result)
        finish = time.perf_counter()
        print(f'Finished simulation in {round(finish-start, 2)} second(s)')
        print('------------------------------------------------------------------------------------------------')
        self.loot = dict(OrderedDict(sorted(loot_dict.items())))

    def save(self):
        if self.loot is not None:
            ts = time.time()
            timestamp_str = str(datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S'))
            filename = './results/loot-simulation-'+timestamp_str+'.json'
            main_dict = {}
            main_dict['monster'] = self.monster
            main_dict['kills'] = self.kills
            main_dict['loot'] = self.loot
            print(f'Saving simulation to file [{filename}]...')
            file = open(filename, "w")
            json.dump(main_dict, file)
            file.close()
        else:
            print('Cannot save None loot. Please run simulate_kills first.')

    def plot_runes(self):
        RUNES = {'r01':0,'r02':0,'r03':0,'r04':0,'r05':0,'r06':0,'r07':0,'r08':0,'r09':0,'r10':0,'r11':0,'r12':0,'r13':0,'r14':0,'r15':0,'r16':0,'r17':0,'r18':0,'r19':0,'r20':0,'r21':0,'r22':0,'r23':0,'r24':0,'r25':0,'r26':0,'r27':0,'r28':0,'r29':0,'r30':0,'r31':0,'r32':0,'r33':0}
        RUNES_TRANSLATION = {'r01':'El','r02':'Eld','r03':'Tir','r04':'Nef','r05':'Eth','r06':'Ith','r07':'Tal','r08':'Ral','r09':'Ort','r10':'Thul','r11':'Amn','r12':'Sol','r13':'Shael','r14':'Dol','r15':'Hel','r16':'Io','r17':'Lum','r18':'Ko','r19':'Fal','r20':'Lem','r21':'Pul','r22':'Um','r23':'Mal','r24':'Ist','r25':'Gul','r26':'Vex','r27':'Ohm','r28':'Lo','r29':'Sur','r30':'Ber','r31':'Jah','r32':'Cham','r33':'Zod'}
        loot_dict = {}
        loot_dict.update(RUNES)
        loot_dict.update(self.get_runes()) #only runes
        plt.figure(figsize=(16, 8))
        plt.bar(range(len(loot_dict)), list(loot_dict.values()), align='center')
        plt.xticks(range(len(loot_dict)), [RUNES_TRANSLATION[loot] for loot in list(loot_dict.keys())])
        sample_size = sum(list(self.loot.values()))
        runes_size = sum(list(loot_dict.values()))
        #title = 'Rune drops from [monster= '+self.monster+'] [kills= '+str(self.kills)+'] [total runes= '+str(runes_size)+'] [total items= '+str(sample_size)+'] [runes%= '+str(runes_size/sample_size*100)[:3]+'%]'
        title = 'Rune drops from '+self.__str__()
        plt.title(title)
        plt.xlabel("item")
        plt.ylabel("drops")
        plt.tick_params(axis='x', which='major', labelsize=8)
        plt.tight_layout()
        plt.show()

    def __str__(self):
        rs = ''
        rs=rs+'[Monster= '+self.monster+']'
        rs=rs+'[Kills= '+str(self.kills)+']'
        item_quantity = sum(list(self.loot.values()))
        runes_quantity = sum(list(self.get_runes().values()))
        runes_percentage = '{:.2f}'.format(runes_quantity/item_quantity*100)
        rs=rs+'[Items= '+str(item_quantity)+']'
        rs=rs+'[Runes= '+str(runes_quantity)+']'
        rs=rs+'[Runes%= '+str(runes_percentage)+']'
        return rs

#####################################
# Global Variables
#####################################
MONSTER = 'Diablo (H)'
KILLS = 15

RUNES = {'r01':0,'r02':0,'r03':0,'r04':0,'r05':0,'r06':0,'r07':0,'r08':0,'r09':0,'r10':0,'r11':0,'r12':0,'r13':0,'r14':0,'r15':0,'r16':0,'r17':0,'r18':0,'r19':0,'r20':0,'r21':0,'r22':0,'r23':0,'r24':0,'r25':0,'r26':0,'r27':0,'r28':0,'r29':0,'r30':0,'r31':0,'r32':0,'r33':0}
RUNES_TRANSLATION = {'r01':'El','r02':'Eld','r03':'Tir','r04':'Nef','r05':'Eth','r06':'Ith','r07':'Tal','r08':'Ral','r09':'Ort','r10':'Thul','r11':'Amn','r12':'Sol','r13':'Shael','r14':'Dol','r15':'Hel','r16':'Io','r17':'Lum','r18':'Ko','r19':'Fal','r20':'Lem','r21':'Pul','r22':'Um','r23':'Mal','r24':'Ist','r25':'Gul','r26':'Vex','r27':'Ohm','r28':'Lo','r29':'Sur','r30':'Ber','r31':'Jah','r32':'Cham','r33':'Zod'}
    
#####################################
# Main
#####################################
if __name__ == '__main__':

    treasureClass = TreasureClass(MONSTER)
    treasureClass.simulate_kills(KILLS)
    treasureClass.save()
    treasureClass.plot_runes()
    
