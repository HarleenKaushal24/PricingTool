# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 08:52:54 2025

@author: Harleen
"""


import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import BytesIO
import uuid 
#import math
from itertools import product
import random
import re

# -------------------- LOGIN SYSTEM --------------------

USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]

def login(user, pwd):
    return user == USERNAME and pwd == PASSWORD

def login_ui():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login(username, password):
            st.session_state["logged_in"] = True
            st.success("✅ Login successful!")
        else:
            st.error("❌ Invalid username or password.")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_ui()
    st.stop()

# -------------------- MAIN APP STARTS HERE --------------------

# Sharepoint Connection building############### 
TENANT_ID = st.secrets["TENANT_ID"]
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
SHAREPOINT_SITE = st.secrets["SHAREPOINT_SITE"]
FILE_PATH = "/PricingTool/"

# Function to get access token
@st.cache_data  # Cache access token function as it is the same for all requests
def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=payload, headers=headers)
    return response.json().get("access_token")

# Function to fetch Excel file from SharePoint
@st.cache_data  # Cache the SharePoint file-fetching to prevent multiple fetches of the same file
def fetch_excel_from_sharepoint(file_name):
    access_token = get_access_token()
    if not access_token:
        st.error("Failed to authenticate with SharePoint")
        return None
    
    headers = {"Authorization": f"Bearer {access_token}"}
    site_url = f"https://graph.microsoft.com/v1.0/sites/{SHAREPOINT_SITE}"
    site_response = requests.get(site_url, headers=headers)
    sharepoint_site = site_response.json()["id"].split(",")[1]
    
    drive_url = f"https://graph.microsoft.com/v1.0/sites/{sharepoint_site}/drives"
    drive_response = requests.get(drive_url, headers=headers)
    drive_id = drive_response.json()["value"][0]["id"]
    FILE_PATH1 = f"{FILE_PATH}{file_name}.xlsx"
    file_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{FILE_PATH1}:/content"
    response = requests.get(file_url, headers=headers)
    
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        st.error("Failed to fetch file from SharePoint")
        return None
    
# Load and cache data files
@st.cache_data
def load_data():
    name = "RCP"
    excel_file = fetch_excel_from_sharepoint(name)
    df_rcp = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "Wages"
    excel_file = fetch_excel_from_sharepoint(name)
    df_wages = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "SetUpTimes"
    excel_file = fetch_excel_from_sharepoint(name)
    df_SetUpTimes = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "RawIngredients"
    excel_file = fetch_excel_from_sharepoint(name)
    df_RawIngredients = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "RCP_Boms"
    excel_file = fetch_excel_from_sharepoint(name)
    df_RCP_Boms = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "BasesDescription"
    excel_file = fetch_excel_from_sharepoint(name)
    df_Base = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "BasesRunRates"
    excel_file = fetch_excel_from_sharepoint(name)
    df_BaseRR = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "BasesWeights"
    excel_file = fetch_excel_from_sharepoint(name)
    df_BaseW = pd.read_excel(excel_file, engine='openpyxl')
    
    name = "Toppings&ColorCode"
    excel_file = fetch_excel_from_sharepoint(name)
    df_Top = pd.read_excel(excel_file, engine='openpyxl')
    
    return df_rcp, df_wages, df_SetUpTimes, df_RawIngredients, df_RCP_Boms,df_Base,df_BaseRR,df_BaseW,df_Top

def main():
    # Load the data
    df_rcp, df_wages, df_SetUpTimes, df_RawIngredients, df_RCP_Boms,df_Base,df_BaseRR,df_BaseW, df_Top = load_data()

    RCP = pd.merge(df_RCP_Boms, df_rcp, left_on="Item_Code", right_on="Recipe_Item_Code", how="left")
    RCP = RCP.drop_duplicates()

    recipe_machines = RCP['Machine'].dropna().unique()
    
    page = st.sidebar.radio('Navigate:', [ 'Base Selection', 'Results'])

    if page == 'Base Selection':
        
        nmbr=st.number_input("Enter number of cookies in a unit: ")
        cookie_data = pd.DataFrame()
        res=pd.DataFrame()
        random_numbers = random.sample(range(10000000, 99999999),int(nmbr)) 
        
        for i in range(int(nmbr)):
            st.write(f"### Cookie {i+1}")
            st.write(i)
            cookie_name = st.text_input(f"Enter name of cookie {i+1}:")
            
            typ = st.radio("Source of Base", ['Cutter/Waterjet', 'Janssen', 'Depositor','Selmi'] ,key=f"base_selection_{i}" )
                    
            if typ== 'Cutter/Waterjet':   
                base1 = df_Base[df_Base['BSE'].astype(str).str.startswith('1')]
                option = st.selectbox('Please Select the base/shape code', base1['BSE'], key=i, index=None)
                st.session_state["option"] = option
                #st.write("Description of your selection:",base1[base1['BSE']==option]['Description'].values[0])
                qty=st.number_input("Enter the Order Quantity here:", key= f'qty_{i}')
                wt1=df_BaseW[(df_BaseW['Category']=="Cutter" )| (df_BaseW['Category']=="Waterjet" )]            
                del wt1['Category']
                wt= wt1[wt1['BSE']==option].dropna().drop_duplicates()
                
                if qty>0:
                    if wt.shape[0]==1: #must always be true 
                        st.write("Description of your selection:",base1[base1['BSE']==option]['Description'].values[0])
                        wt['Category']="Cutter/Waterjet"
                        dough_wt= wt['Weight(Kg)'].values[0]*qty
                    
                        rcp=st.text_input("Enter the rcp here:", key= f'rcp_{i}')
                        st.session_state["rcp"] = rcp
                        #st.write("Description of your selection:",df_rcp[df_rcp['Recipe_Item_Code']=="RCP"+ rcp])
                        rcp_sel = RCP[RCP['Item_Code'] == "RCP" + rcp]
                        
                        setup = df_SetUpTimes[df_SetUpTimes['Machine'] == "Mixing"]['Shift SetUp Time(mins)'].iloc[0]
                        mixwage = df_wages[df_wages['Description'] == "Mixing"]['Value'].iloc[0]
                        
                        rcp_sel['BatchSize/Kg'] = rcp_sel['IngredientQuantity'] / rcp_sel['BatchSize']
                        rcp_sel['IngQty'] = rcp_sel['BatchSize/Kg'] * rcp_sel['Recipe_Batch_Size_KG']
                        rcp_sel_cost = pd.merge(rcp_sel, df_RawIngredients, left_on="IngredientID", right_on="Item No.", how="left")  
                        rcp_sel_cost['MaterialCost/Batch'] = rcp_sel_cost['IngQty'] * rcp_sel_cost['Last Evaluated Price (/kg)']
                        rcp_sel_cost['%Ingredients'] = round(rcp_sel_cost['IngredientQuantity'] * 100 / rcp_sel_cost['BatchSize'], 3)            
                        rcp_sel_cost1 = rcp_sel_cost.groupby(['Item_Code', 'Recipe_Batch_Size_KG', 'Machine', 'Number_of_Mixers_Operators_Required', 'Minutes_Batch'])['MaterialCost/Batch'].sum()
                        rcp_sel_cost2 = pd.DataFrame(rcp_sel_cost1.reset_index())           
                        rcp_sel_cost2['Labour&SetupCost/Batch'] = rcp_sel_cost2['Number_of_Mixers_Operators_Required'] * mixwage * (setup + rcp_sel_cost2['Minutes_Batch']) / 60
                        rcp_sel_cost2['TotalCost/Batch'] = rcp_sel_cost2['MaterialCost/Batch'] + rcp_sel_cost2['Labour&SetupCost/Batch']
                        
                        rcp_sel_cost2['MaterialCost/Kg'] = rcp_sel_cost2['MaterialCost/Batch'] / rcp_sel_cost2['Recipe_Batch_Size_KG']
                        rcp_sel_cost2['Labour&SetupCost/Kg'] = rcp_sel_cost2['Labour&SetupCost/Batch'] / rcp_sel_cost2['Recipe_Batch_Size_KG']
                        rcp_sel_cost2['TotalCost/Kg'] = rcp_sel_cost2['TotalCost/Batch'] / rcp_sel_cost2['Recipe_Batch_Size_KG']
                       
                        rcp_sel_cost2['MaterialCost/Qty_Reqd'] = rcp_sel_cost2['MaterialCost/Kg'] * dough_wt
                        rcp_sel_cost2['Labour&SetupCost/Qty_Reqd'] = rcp_sel_cost2['Labour&SetupCost/Kg'] * dough_wt
                        rcp_sel_cost2['TotalCost/Qty_Reqd'] = rcp_sel_cost2['TotalCost/Kg'] * dough_wt
                        
                        rcp_sel_cost2['MaterialCost/Cookie'] = rcp_sel_cost2['MaterialCost/Qty_Reqd'] / qty
                        rcp_sel_cost2['Labour&SetupCost/Cookie'] = rcp_sel_cost2['Labour&SetupCost/Qty_Reqd'] / qty
                        rcp_sel_cost2['TotalCost/Cookie'] = rcp_sel_cost2['TotalCost/Qty_Reqd']/ qty
                        
                        if 'show_ingredients' not in st.session_state:
                            st.session_state.show_ingredients = False

                        # Use unique keys for buttons to avoid conflicts
                        show_key = f"show_{i}_ingredients"
                        hide_key = f"hide_{i}_ingredients"
                        # Show or hide ingredients for each cookie independently
                        if st.button("Show Ingredients", key=show_key):
                            st.session_state.show_ingredients = True
            
                        if st.button("Hide Ingredients", key=hide_key):
                            st.session_state.show_ingredients= False
            
                        # Show ingredients if the flag is True for this cookie
                        if st.session_state.show_ingredients:
                            Ing = rcp_sel_cost[['Ingredients', 'Item Description', 'IngQty', 'Last Evaluated Price (/kg)', 
                                                'Recipe_Batch_Size_KG', 'Minutes_Batch']].drop_duplicates()
                            Ing["Setup Time"] = setup
                            Ing["Mixer Wage"] = mixwage
                            Ing['MaterialCost/Qty_Reqd']=rcp_sel_cost2['MaterialCost/Qty_Reqd'].values[0]
                            Ing['Labour&SetupCost/Qty_Reqd']=rcp_sel_cost2['Labour&SetupCost/Qty_Reqd'].values[0]
                            st.write(Ing)
                                
                        
                                        
                        rcp_sel_cost3=rcp_sel_cost2[['Item_Code', 'MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd',
                               'TotalCost/Qty_Reqd', 'MaterialCost/Cookie',
                               'Labour&SetupCost/Cookie', 'TotalCost/Cookie']].drop_duplicates()
                        rcp_sel_cost3['People']=1
                        rcp_sel_cost3['Stage']="Dough Mixing"
                        
                        if (rcp_sel_cost3.shape[0]==1) and (rcp_sel_cost2.shape[0] >1):
                            rcp_sel_cost3['Machine']= ', '.join(rcp_sel_cost2['Machine'].astype(str))
                        else: rcp_sel_cost3['Machine']=rcp_sel_cost2['Machine']
                            
                        
                        #rcp_sel_cost3['Name']=cookie_name
                        
                        rr_base=df_BaseRR[df_BaseRR["BSE"]==option]
                        
                        #bake:
                        sup,oven,binn=1,1,1 
                        w_sup= df_wages[df_wages['Description']=="Line Supervisor"]['Value'].values[0]
                        #w_oven= df_wages[df_wages['Description']=="Baking"]['Value'].values[0]
                        w1= df_wages[df_wages['Description']=="Cookie Cutting"]['Value'].values[0]
                        
                        setup_b=df_SetUpTimes[df_SetUpTimes['Machine']=="Cutter/Waterjet"]['Shift SetUp Time(mins)'].values[0]
                        
                        b_rr1 = rr_base[(rr_base["Machine"]=="Cutter") | (rr_base["Machine"]=="Waterjet")]
                        b_rr=b_rr1.drop(columns=['Loader', 'Catcher'])
                        b_rr = b_rr.dropna()
                        b_rr3 = pd.DataFrame()
                        for j in range(b_rr.shape[0]):
                            b_rr2= b_rr.iloc[[j]]
                            #st.write("If run on ",b_rr2['Machine'].values[0])
                            b_rr2['JobTime']= 1*60*qty/b_rr2['RunRate(CookiesPerHour)']
                            b_rr2['Labour&SetupCost/Qty_Reqd'] = ((b_rr2['People'] + binn/2 + oven/2)*w1 + sup*w_sup/2) * (setup_b + b_rr2['JobTime']) / 60  #assuming both cutter and waterjet are working so line supervisor's wage is balaced nbetween 2 machines
                            b_rr2['Labour&SetupCost/Cookie'] = b_rr2['Labour&SetupCost/Qty_Reqd']/ qty
                            #st.write(b_rr2)
                            b_rr3 = pd.concat([b_rr3,b_rr2], axis=0, ignore_index=True)
                        
                        b_rr3 = b_rr3.rename({'BSE': 'Item_Code'}, axis=1)
                        b_rr3['MaterialCost/Qty_Reqd']=0
                        b_rr3['TotalCost/Qty_Reqd']= b_rr3['MaterialCost/Qty_Reqd']+ b_rr3['Labour&SetupCost/Qty_Reqd']
                        b_rr3['MaterialCost/Cookie']=0
                        b_rr3['TotalCost/Cookie']= b_rr3['MaterialCost/Cookie']+ b_rr3['Labour&SetupCost/Cookie']
                        b_rr3['Stage']= "Baking"
                        
                        comb1=pd.concat([rcp_sel_cost3,b_rr3], axis=0, ignore_index=True)
                        comb1['Department']="Baking"
                        comb1['Operator']="None"
         ###############################################################################################################
        
                
                        #enrob:
                        st.write(i)
                        w2= df_wages[df_wages['Description']=="Enrobing"]['Value'].values[0]
                        if f"enrobing_{i}" not in st.session_state:
                            st.session_state[f"enrobing_{i}"] = False
                            
                        comb2=pd.DataFrame() 
                        st.write(random_numbers[i])
                        en = st.checkbox("Enrobing", disabled=False, label_visibility="visible", value=True, key=f"enrobing_{i}")
                        if en:
                            sup_en = 1
                             
                            #RCP colour costs
                            rcp_col = st.text_input("Please enter 3 digit RCP id with flavour if any (XXX.flav or XXX)",  key=f"rcp_col_{i}")
                            rcp_col_sel = RCP[RCP['Item_Code'] == "RCP" + str(rcp_col)]
                            if rcp_col_sel.shape[0]>0:
                                st.write("Description of your selection:",rcp_col_sel[rcp_col_sel['Item_Code']=="RCP" + str(rcp_col)]['Description'].values[0])
                            else: st.write("No colour selected")
                            setupcol=0
                              
                            rcp_col_sel['BatchSize/Kg'] = rcp_col_sel['IngredientQuantity'] / rcp_col_sel['BatchSize']
                            rcp_col_sel['IngQty'] = rcp_col_sel['BatchSize/Kg'] * rcp_col_sel['Recipe_Batch_Size_KG']
                
                            rcp_col_sel_cost = pd.merge(rcp_col_sel, df_RawIngredients, left_on="IngredientID", right_on="Item No.", how="left")
                            
                            rcp_col_sel_cost['MaterialCost/Batch'] = rcp_col_sel_cost['IngQty'] * rcp_col_sel_cost['Last Evaluated Price (/kg)']
                            rcp_col_sel_cost['%Ingredients'] = round(rcp_col_sel_cost['IngredientQuantity'] * 100 / rcp_col_sel_cost['BatchSize'], 3)                
                            rcp_col_sel_cost['TotalMaterialCost/Batch']  = rcp_col_sel_cost['MaterialCost/Batch'].sum()
                               
                            rcp_col_sel_cost['Labour&SetupCost/Batch'] = rcp_col_sel_cost['Number_of_Mixers_Operators_Required'] * w2 * (setupcol + rcp_col_sel_cost['Minutes_Batch']) / 60
                            rcp_col_sel_cost['Labour&SetupCost/Kg'] = rcp_col_sel_cost['Labour&SetupCost/Batch'] / rcp_col_sel_cost['Recipe_Batch_Size_KG']
                            rcp_col_sel_cost['TotalMaterialCost/Kg'] = rcp_col_sel_cost['TotalMaterialCost/Batch'] / rcp_col_sel_cost['Recipe_Batch_Size_KG'] 
                           
                            rcp_col_sel_cost1= rcp_col_sel_cost[['Item_Code', 'Description','Labour&SetupCost/Kg','TotalMaterialCost/Kg']].drop_duplicates()
                            
                            #Enrobing Costs
                                
                            set_up_en= df_SetUpTimes[df_SetUpTimes['Department']=='Enrobing']
                            
                            wt2=df_BaseW[(df_BaseW['Category']=="Enrobing Material") & (df_BaseW['BSE']==option)]['Weight(Kg)'].values[0] 
                            
                            ###################
                            rcp_col_sel_cost1['MaterialCost/Qty_Reqd']=rcp_col_sel_cost1['TotalMaterialCost/Kg']* (qty*wt2)
                            rcp_col_sel_cost1['Labour&SetupCost/Qty_Reqd']= rcp_col_sel_cost1['Labour&SetupCost/Kg']* (qty*wt2)
                            rcp_col_sel_cost1['TotalCost/Qty_Reqd']=rcp_col_sel_cost1['MaterialCost/Qty_Reqd'] + rcp_col_sel_cost1['Labour&SetupCost/Qty_Reqd']
                            rcp_col_sel_cost1['MaterialCost/Cookie']=rcp_col_sel_cost1['MaterialCost/Qty_Reqd']/ qty
                            rcp_col_sel_cost1['Labour&SetupCost/Cookie']= rcp_col_sel_cost1['Labour&SetupCost/Qty_Reqd'] /qty
                            rcp_col_sel_cost1['TotalCost/Cookie']= rcp_col_sel_cost1['MaterialCost/Cookie']+rcp_col_sel_cost1['Labour&SetupCost/Cookie']
                            rcp_col_sel_cost2=rcp_col_sel_cost1[['Item_Code', 'MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd',
                                   'TotalCost/Qty_Reqd', 'MaterialCost/Cookie', 'Labour&SetupCost/Cookie','TotalCost/Cookie']]
                            rcp_col_sel_cost2['People']=1
                            rcp_col_sel_cost2['Stage']= "Colour Mixing (E)"
                            rcp_col_sel_cost2['Machine']= "Colour Mixers"
                            # Ing1 = rcp_col_sel_cost[['Ingredients', 'IngQty', 'Last Evaluated Price (/kg)', 
                            #                     'Recipe_Batch_Size_KG', 'Minutes_Batch']].drop_duplicates()
                            
                            # Ing1["Setup Time"] = setupcol
                            # Ing1["Mixer Wage"] = w2
                            # Ing1['MaterialCost/Qty_Reqd']=rcp_col_sel_cost1['MaterialCost/Qty_Reqd'].values[0]
                            # Ing1['Labour&SetupCost/Qty_Reqd']=rcp_col_sel_cost1['Labour&SetupCost/Qty_Reqd'].values[0]
                            # st.write(Ing1)
                            
                            ##################
                            
                            e_rr1 = rr_base[(rr_base["Machine"]!="Cutter") & (rr_base["Machine"]!="Waterjet")].dropna()
                            e_rr=e_rr1.drop(columns=['Loader', 'Catcher'])
                            
                            
                            
                            if f"top_{i}" not in st.session_state:
                                st.session_state[f"top_{i}"] = False
                            if f"m_{i}" not in st.session_state:
                                st.session_state[f"m_{i}"] = "Machine"
                                                           
                            tp= st.checkbox("Toppings", disabled=False, label_visibility="visible", key=f'top_{i}',value=True)
                            if tp:
                                sp = st.radio('Sprinkler:', ['Machine', 'Person'], horizontal=True, key=f"m_{i}")
                                sprinkler = 0 if sp == "Machine" else 1
                            
                                n_tp = st.number_input("Number of Toppings:", min_value=0, step=1, format="%d",key=f"num_toppings_{i}")
                            
                                t_codes1 = []
                                t_prices1 = []
                                t_qty1 = []
                            
                                for t in range(int(n_tp)):
                                    # Ensure consistent session state keys
                                    qty_key = f"qty2_{i}_{t}"
                                    unit_key = f"u_{i}_{t}"
                                    option_key = f"option_{i}_{t}"
                            
                                    if qty_key not in st.session_state:
                                        st.session_state[qty_key] = 0
                                    if unit_key not in st.session_state:
                                        st.session_state[unit_key] = 'Kg'
                            
                                    tp1 = df_Top[df_Top['Colour'] == "Sprinkles"]
                                    option11 = st.selectbox('Please Select the topping code', tp1['Code'], key=option_key, index=None)  
                            
                                    if option11 and option11 in df_RawIngredients["Item No."].values:
                                        tp_price1 = df_RawIngredients.loc[df_RawIngredients["Item No."] == option11, 'Last Evaluated Price (/kg)']
                                        tp_price1 = tp_price1.iloc[0] if not tp_price1.empty else 0
                                        st.write("Description of your selection:", tp1[tp1['Code'] == option11]['Description'].values[0])
                                    else: 
                                        tp_price1 = 0
                                        st.write("Provide Topping Code")
                            
                                    qty1 = st.number_input("Enter the topping Quantity here:", step=0.001, format="%0.3f", key=qty_key)
                                    u1 = st.radio("Units of measurement", ['Kg', 'grams'], key=unit_key, horizontal=True)
                            
                                    qty21 = qty1 if u1 == 'Kg' else qty1 / 1000
                                    t_qty1.append(qty21)
                                    t_prices1.append(tp_price1)
                                    if option11:
                                        t_codes1.append(option11)
                            
                                qty2 = sum(t_qty1)
                                tp_price = sum(x * y for x, y in zip(t_prices1, t_qty1))
                                option1 = ', '.join(t_codes1) if t_codes1 else "No Toppings Selected"
                            else: option1,qty2,tp_price,sprinkler = 0,0,0,0
                            
                            e_rr["ToppingCode"]= option1
                            e_rr["TotalToppingQty"]= qty2 * qty
                            e_rr["TotalEnrobingMaterialW"]=wt2 * qty
                            e_rr["TotalToppingPrice"]=e_rr["TotalToppingQty"] * tp_price
                            e_rr["MaterialCost/Qty_Reqd"]= e_rr["TotalToppingPrice"]
                        
                            e_rr2=pd.merge(e_rr, set_up_en.iloc[:, 1:3], left_on="Machine", right_on="Machine", how="left")
                            
                            e_rr2['JobTime']= 1*60*qty/e_rr2['RunRate(CookiesPerHour)']
                            e_rr2['Labour&SetupCost/Qty_Reqd'] = ((e_rr2['People']+ sprinkler)*w2 + sup_en*w_sup/3 )* (e_rr2['Shift SetUp Time(mins)'] + e_rr2['JobTime']) / 60    #assuming atleast 3 machines are working so line supervisor's wage is balanced among 3 machines
                            # e_rr2["TotalLabour&SetupCost"]= e_rr2['TotalRCP_Labour&SetupCost'] + e_rr2['Labour&SetupCost']
                            e_rr2['TotalCost/Qty_Reqd']=e_rr2['Labour&SetupCost/Qty_Reqd']+e_rr2["MaterialCost/Qty_Reqd"]
                            e_rr2["MaterialCost/Cookie"]=e_rr2["MaterialCost/Qty_Reqd"]/qty
                            e_rr2["Labour&SetupCost/Cookie"]=e_rr2["Labour&SetupCost/Qty_Reqd"]/qty
                            e_rr2['TotalCost/Cookie']=e_rr2['TotalCost/Qty_Reqd']/qty
                            
                            e_rr2 = e_rr2.rename({'BSE': 'Item_Code'}, axis=1)
                            e_rr3=e_rr2[['Item_Code', 'MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd','TotalCost/Qty_Reqd',
                                         'MaterialCost/Cookie', 'Labour&SetupCost/Cookie','TotalCost/Cookie','People','Machine',
                                         'RunRate(CookiesPerHour)', 'JobTime']]
                            e_rr3['Stage']='Enrobing'
                            
                            comb2=pd.concat([rcp_col_sel_cost2,e_rr3], axis=0, ignore_index=True)
                            comb2['Department']="Enrobing"
                            comb2['Operator']="None"
                        else:
                            comb2[['Item_Code','MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd', 'TotalCost/Qty_Reqd',
                                'MaterialCost/Cookie', 'Labour&SetupCost/Cookie', 'TotalCost/Cookie',
                                'People', 'Operator','Stage', 'Machine', 'RunRate(CookiesPerHour)', 'JobTime']]=0
                            comb2['Department']="Enrobing"
                        
                        #st.write(comb2)
                        
                        #Robot
                        sup_rob = 1
                        comb3=pd.DataFrame() 
                        setupcol_rob=0
                        w_op_rob = df_wages[df_wages['Description']=='Deco Robot']['Value'].values[0]
                        w_rob = df_wages[df_wages['Description']=='Cookie load/unloader']['Value'].values[0]
                        if f"bot_{i}" not in st.session_state:
                            st.session_state[f"bot_{i}"] = "0"
                        bot_col = st.radio('#Colours for Deco:', ['0', '1','2','3','4','5','6'], horizontal=True, key=f"bot_{i}")
                        bot_col= int(bot_col)
                        rob_col_qty=[]
                        rcp_col_rob_cost2=pd.DataFrame()
                        if bot_col >0:
                            rcp_col_rob_cost=pd.DataFrame()
                            rcp_col_rob_sel_cost2=pd.DataFrame()
                            for b in range(bot_col):
                                qty_key1 = f"col_qty2_{i}_{b}"
                                unit_key1 = f"col_u_{i}_{b}"
                                option_key1 = f"col_option_{i}_{b}"
                        
                                if qty_key1 not in st.session_state:
                                    st.session_state[qty_key1] = 0
                                if unit_key1 not in st.session_state:
                                    st.session_state[unit_key1] = 'Kg'
                                
                                rcp_col_rob = st.text_input("Please enter 3 digit Colour id ",  key=f"rcp_col_rob_{i}_{b}")
                                rcp_col_rob_sel = RCP[RCP['Item_Code'] == "RCP" + str(rcp_col_rob) + ".PS"]
                                if rcp_col_rob_sel.shape[0]>0:
                                    st.write("Description of your selection:",rcp_col_rob_sel[rcp_col_rob_sel['Item_Code']=="RCP" + str(rcp_col_rob) + ".PS"]['Description'].values[0])
                                    col_qty = st.number_input("Enter the Colour Quantity here:", step=0.001, format="%0.3f", key=qty_key1)                       
                                    u_rob = st.radio("Units of measurement", ['Kg', 'grams'], key=unit_key1, horizontal=True)
                            
                                    col_qty2= col_qty if u_rob == 'Kg' else col_qty / 1000
  
                                    col_order_qty2= col_qty2*qty
                                    #rob_col_qty.append(col_qty2)                                
                                      
                                    rcp_col_rob_sel['BatchSize/Kg'] = rcp_col_rob_sel['IngredientQuantity'] / rcp_col_rob_sel['BatchSize']
                                    rcp_col_rob_sel['IngQty'] = rcp_col_rob_sel['BatchSize/Kg'] * rcp_col_rob_sel['Recipe_Batch_Size_KG']
                                    
                                    col_order_batch=-(-col_order_qty2 // rcp_col_rob_sel['Recipe_Batch_Size_KG'].values[0])
                                    st.write("#Batches of RCP" + str(rcp_col_rob) + ".PS: ", col_order_batch)
                                    
                                    rcp_col_rob_sel_cost = pd.merge(rcp_col_rob_sel, df_RawIngredients, left_on="IngredientID", right_on="Item No.", how="left")
                                                 
                                    rcp_col_rob_sel_cost['MaterialCost/Batch'] = rcp_col_rob_sel_cost['IngQty'] * rcp_col_rob_sel_cost['Last Evaluated Price (/kg)']
                                    rcp_col_rob_sel_cost['%Ingredients'] = round(rcp_col_rob_sel_cost['IngredientQuantity'] * 100 / rcp_col_rob_sel_cost['BatchSize'], 3)                
                                    rcp_col_rob_sel_cost['TotalMaterialCost/Batch']  = rcp_col_rob_sel_cost['MaterialCost/Batch'].sum()
                                    rcp_col_rob_sel_cost['MaterialCost/Reqd_Qty']  = rcp_col_rob_sel_cost['MaterialCost/Batch']*col_order_batch
                                    rcp_col_rob_sel_cost['TotalMaterialCost/Reqd_Qty']  = rcp_col_rob_sel_cost['MaterialCost/Reqd_Qty'].sum()
                                    
                                    rcp_col_rob_sel_cost['Labour&SetupCost/Batch'] = rcp_col_rob_sel_cost['Number_of_Mixers_Operators_Required'] * w2 * (setupcol_rob + rcp_col_rob_sel_cost['Minutes_Batch']) / 60
                                    rcp_col_rob_sel_cost['Labour&SetupCost/Reqd_Qty'] = rcp_col_rob_sel_cost['Labour&SetupCost/Batch'] * col_order_batch
                                                                       
                                    rcp_col_rob_sel_cost1= rcp_col_rob_sel_cost[['Ingredients','IngQty','Last Evaluated Price (/kg)','MaterialCost/Batch','MaterialCost/Reqd_Qty','Labour&SetupCost/Batch','Labour&SetupCost/Reqd_Qty']].drop_duplicates()
                                    st.write(rcp_col_rob_sel_cost1)
                                    rcp_col_rob_sel_cost2= rcp_col_rob_sel_cost[['Item_Code','Description','TotalMaterialCost/Reqd_Qty','Labour&SetupCost/Reqd_Qty']].drop_duplicates()
                                    rcp_col_rob_cost=pd.concat([rcp_col_rob_cost,rcp_col_rob_sel_cost2], axis=0, ignore_index=True)
                                    
                                    rcp_col_rob_cost1=rcp_col_rob_cost
                                    rcp_col_rob_cost1['Item_Code']=', '.join(rcp_col_rob_cost['Item_Code'])
                                    rcp_col_rob_cost1['MaterialCost/Qty_Reqd']= sum(rcp_col_rob_cost['TotalMaterialCost/Reqd_Qty'])
                                    rcp_col_rob_cost1['Labour&SetupCost/Qty_Reqd']= sum(rcp_col_rob_cost['Labour&SetupCost/Reqd_Qty'])
                                    
                                    rcp_col_rob_cost1['TotalCost/Qty_Reqd']= rcp_col_rob_cost1['MaterialCost/Qty_Reqd']+rcp_col_rob_cost1['Labour&SetupCost/Qty_Reqd']
                                    rcp_col_rob_cost1['MaterialCost/Cookie']= rcp_col_rob_cost1['MaterialCost/Qty_Reqd']/qty
                                    rcp_col_rob_cost1['Labour&SetupCost/Cookie']= rcp_col_rob_cost1['Labour&SetupCost/Qty_Reqd']/qty
                                    rcp_col_rob_cost1['TotalCost/Cookie']= rcp_col_rob_cost1['MaterialCost/Cookie']+rcp_col_rob_cost1['Labour&SetupCost/Cookie']
                                    rcp_col_rob_cost2=rcp_col_rob_cost1[['Item_Code', 'MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd',
                                           'TotalCost/Qty_Reqd', 'MaterialCost/Cookie', 'Labour&SetupCost/Cookie','TotalCost/Cookie']].drop_duplicates()
                                    rcp_col_rob_cost2['People']=1
                                    rcp_col_rob_cost2['Stage']= "Colour Mixing (R)"
                                    rcp_col_rob_cost2['Machine']= "Colour Mixers"
                                    rcp_col_rob_cost2['Operator']= "None"
                                    
                                else: st.write("No colour selected")
                                
                            ##if robot colour but outside for loop
                            st.write("Total cost of robot RCPs")
                            st.write(rcp_col_rob_cost)
                            set_up_rb= df_SetUpTimes[df_SetUpTimes['Department']=='Robot']
                            
                            if f"top_rob_{i}" not in st.session_state:
                                st.session_state[f"top_rob_{i}"] = False                               
                            
                            option11r =""
                            tp_rb= st.checkbox("Robot Toppings", disabled=False, label_visibility="visible", key=f'top_rob_{i}',value=True)
                            if tp_rb:
                                n_tp_rb = st.number_input("Number of Toppings:", min_value=0, step=1, format="%d",key=f"num_rob_toppings_{i}")                          
                                t_codes1_r = []
                                t_prices1_r = []
                                t_qty1_r = []                           
                                for r in range(int(n_tp_rb)):

                                    qty_key_r = f"qty_r_{i}_{r}"
                                    unit_key_r = f"u_r_{i}_{r}"
                                    option_key_r = f"option_r_{i}_{r}"
                            
                                    if qty_key_r not in st.session_state:
                                        st.session_state[qty_key_r] = 0
                                    if unit_key_r not in st.session_state:
                                        st.session_state[unit_key_r] = 'Kg'
                            
                                    tp_r1 = df_Top[df_Top['Colour'] == "Sprinkles"]
                                    option1r = st.selectbox('Please Select the topping code', tp_r1['Code'], key=option_key_r, index=None)  
                            
                                    if option1r and option1r in df_RawIngredients["Item No."].values:
                                        tp_price1_r = df_RawIngredients.loc[df_RawIngredients["Item No."] == option1r, 'Last Evaluated Price (/kg)']
                                        tp_price1_r = tp_price1_r.iloc[0] if not tp_price1_r.empty else 0
                                        st.write("Description of your selection:", tp_r1[tp_r1['Code'] == option1r]['Description'].values[0])
                                    else: 
                                        tp_price1_r = 0
                                        qty21_r=0
                                        st.write("Provide Topping Code")
                            
                                    qty1_r = st.number_input("Enter the topping Quantity here:", step=0.001, format="%0.3f", key=qty_key_r)
                                    u1_r = st.radio("Units of measurement", ['Kg', 'grams'], key=unit_key_r, horizontal=True)
                            
                                    qty21_r = qty1_r if u1_r == 'Kg' else qty1_r / 1000
                                    t_qty1_r.append(qty21_r)
                                    t_prices1_r.append(tp_price1_r)
                                    if option1r:
                                        t_codes1_r.append(option1r)
                                
                                if len(t_codes1_r)==n_tp_rb:
                                    qty2r = sum(t_qty1_r)
                                    tp_pricer = sum(x * y for x, y in zip(t_prices1_r, t_qty1_r))
                                    option11r = ', '.join(t_codes1_r)
                                    rob_t=pd.DataFrame({"Topping":t_codes1_r,"Price/Kg":t_prices1_r,"Quantity/Cookie(kg)":t_qty1_r})
                                    rob_t['TotalPrice']=rob_t['Price/Kg']*rob_t['Quantity/Cookie(kg)']*qty
                                    st.write(rob_t)
                                    

                            else: 
                                option11r =""
                                rob_t=pd.DataFrame({"Topping":[0],"Price/Kg":[0],"Quantity/Cookie(kg)":[0],"TotalPrice":[0]})
                                #st.write(rob_t)
                                
                            num_extras = st.number_input("Enter number of extra ppl (sprinklers/builders)", min_value=0, step=1,key=f"num_ex_{i}")
                            num_scenarios = st.number_input("Enter number of scenarios for robot Run Rates:", min_value=0, step=1,key=f"num_scen_{i}")
                            
                            # Set up empty DataFrame structure
                            columns = ["Robot Number", "# of Loaded Cookies", "No. of Loaders", 
                                       "No. of Catchers", "No. of Operators", "# of Heads or Bots", "Production Rate"]
                            
                            default_data = pd.DataFrame([["", 0, 0, 0, 0, 0, 0.0]] * num_scenarios, columns=columns)
                            
                            #st.subheader("Fill or edit your data below:")
                            st.write("Fill or edit Robot Spec data below:")
                            edited_df = st.data_editor(default_data, num_rows="fixed",key=f"data_editor_{i}")
                            
                            edited_df['RunRates2secTrans']=edited_df['Production Rate']+2000
                            edited_df['RunRates']=round(60*60*1000*edited_df['# of Loaded Cookies']/edited_df['RunRates2secTrans'],0)
                            edited_df['People']=edited_df['No. of Loaders'] + edited_df['No. of Catchers'] + num_extras
                            st.write("Robot Run Rates:")
                            st.write(edited_df)
                            #st.write(option11r)
                        #else bot_col >4:
                            rob_rr=edited_df
                            rob_rr['Robot Number'] = rob_rr['Robot Number'].str.split(' or ')
                            rob_rr = rob_rr.explode('Robot Number', ignore_index=True)
                            rob_rr['Robot Number'] = "R"+rob_rr['Robot Number']
                            
                            rob_rr["ToppingCode"]= option11r
                            rob_rr["MaterialCost/Qty_Reqd"]= sum( rob_t['TotalPrice']) if 'rob_t' in locals() else 0

                            rob_rr2=pd.merge(rob_rr, set_up_rb.iloc[:, 1:3], left_on="Robot Number", right_on="Machine", how="left")
                            
                            rob_rr2['JobTime']= 1*60*qty/rob_rr2['RunRates']
                            rob_rr2['Labour&SetupCost/Qty_Reqd'] = ((rob_rr2['People'])*w_rob + sup_rob*w_sup/3 + (rob_rr2['No. of Operators'])*w_op_rob )* (rob_rr2['Shift SetUp Time(mins)'] + rob_rr2['JobTime']) / 60    #assuming all 3 machines are working so line supervisor's wage is balanced among 3 machines
                            rob_rr2['TotalCost/Qty_Reqd']=rob_rr2['Labour&SetupCost/Qty_Reqd']+rob_rr2["MaterialCost/Qty_Reqd"]
                            rob_rr2["MaterialCost/Cookie"]=rob_rr2["MaterialCost/Qty_Reqd"]/qty
                            rob_rr2["Labour&SetupCost/Cookie"]=rob_rr2["Labour&SetupCost/Qty_Reqd"]/qty
                            rob_rr2['TotalCost/Cookie']=rob_rr2['TotalCost/Qty_Reqd']/qty
                            
                            rob_rr2['Item_Code']=option
                            
                            rob_rr2 = rob_rr2.rename({'No. of Operators': 'Operator', 'RunRates':'RunRate(CookiesPerHour)'}, axis=1)
                            rob_rr3=rob_rr2[['Item_Code', 'MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd','TotalCost/Qty_Reqd',
                                        'MaterialCost/Cookie', 'Labour&SetupCost/Cookie','TotalCost/Cookie','People','Operator','Machine',
                                        'RunRate(CookiesPerHour)', 'JobTime']]
                            rob_rr3['Stage']='Decorating'
                           

                            comb3=pd.concat([rcp_col_rob_cost2,rob_rr3], axis=0, ignore_index=True)
                            comb3['Department']="Robot"
                            # st.write(rob_rr3)
                            # st.write(rcp_col_rob_cost2)
                        else:
                            comb3[['Item_Code','MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd', 'TotalCost/Qty_Reqd',
                                'MaterialCost/Cookie', 'Labour&SetupCost/Cookie', 'TotalCost/Cookie',
                                'People', 'Operator','Stage', 'Machine', 'RunRate(CookiesPerHour)', 'JobTime']]=0
                            comb3['Department']="Robot"     
                        
                        dept_comb1=pd.concat([comb1,comb2,comb3], axis=0, ignore_index=True)                       
                        dept_comb1['Name']= cookie_name
                        dept_comb1['OrderQty']=qty
                        dept_comb1=dept_comb1[['Name','OrderQty','Item_Code','Department','Stage', 'Machine','People','MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd', 'TotalCost/Qty_Reqd',
                            'MaterialCost/Cookie', 'Labour&SetupCost/Cookie', 'TotalCost/Cookie',
                             'Operator', 'RunRate(CookiesPerHour)', 'JobTime']]
                    
                else: 
                    dept_comb1=pd.DataFrame()  
                    dept_comb1['Name']= cookie_name
                    dept_comb1['OrderQty']=0
                    
                cookie_data=pd.concat([cookie_data,dept_comb1], axis=0, ignore_index=True)
        
        st.divider()
        st.markdown(f":red-background['Results: Prices per stage']") 
        st.write(cookie_data)
        st.divider()
        if res not in st.session_state:
            st.session_state.res = False
 
        if st.button("Show: Prices per complete route"):
            st.session_state.res = True

        if st.button("Hide"):
            st.session_state.res= False

        if st.session_state.res:
            cookie_data_fixed=cookie_data[cookie_data['RunRate(CookiesPerHour)'].isna()]
            cookie_data_routes=cookie_data[cookie_data['RunRate(CookiesPerHour)'].notna()]
            cookies=cookie_data['Name'].unique()
            for k in range(int(nmbr)):
                cookie_data_fixed1=cookie_data_fixed[cookie_data_fixed['Name']==cookies[k]]
                cookie_data_routes1=cookie_data_routes[cookie_data_routes['Name']==cookies[k]]
                cookie_order=cookie_data_routes[cookie_data_routes['Name']==cookies[k]]['OrderQty'].iloc[0]
                 # Group data by department
                department_groups = cookie_data_routes1.groupby("Department")[['Machine', 'TotalCost/Qty_Reqd', 'JobTime','People']].apply(lambda x: x.values.tolist())
                
                department_combinations = list(product(*department_groups))
                
                # Calculate total cost and job time for each combination
                results1 = []
                for combination in department_combinations:
                    total_cost = 0
                    total_time = 0
                    people_count = []
                    
                    for machine in combination:
                        total_cost += machine[1]  # Cost for each machine
                        total_time += machine[2]  # Job time for each machine
                        people_count.append(machine[3])  # Number of people for each machine
                    
                    # Concatenate machine names and people count for output
                    machine_combo = " + ".join(f"{machine[0]} (People: {machine[3]})" for machine in combination)
                    
                    
                    results1.append((machine_combo,  total_cost, total_time))
                
                # Convert results to DataFrame and sort
                result_df = pd.DataFrame(results1, columns=["Route", "Route Cost", "Route Job Time"])
                result_df = result_df.sort_values(by=["Route Cost", "Route Job Time"])  # Sort by cost, then time
                result_df['Name']= cookies[k]
                result_df['OrderQty']= cookie_order
                
                def extract_machine_people(rout):
                    pattern = r'([A-Za-z0-9]+)\s?\(People:\s?(\d+)\)'
                    matches = re.findall(pattern, rout)
                    
                    # Dictionary to store machine and people counts
                    machine_dict = {'M1': '', 'M2': '', 'M3': ''}
                    
                    for machine, people in matches:
                        people = int(people)
                        
                        # Map machines to respective columns M1, M2, M3
                        if machine in ['Cutter', 'Waterjet']:  
                            machine_dict['M1'] = f'{machine} {people}'
                        elif machine.startswith('E'): 
                            machine_dict['M2'] = f'{machine} {people}'
                        elif machine.startswith('R'): 
                            machine_dict['M3'] = f'{machine} {people}'
                    
                    return machine_dict
                

                result_df[['M1', 'M2', 'M3']] = result_df['Route'].apply(extract_machine_people).apply(pd.Series) 
                
                def get_cost(machine_people_str):
                    if machine_people_str:
                        parts = machine_people_str.split()
                        if len(parts) == 2:
                            machine, people = parts[0], int(parts[1])
                            match = cookie_data_routes1[(cookie_data_routes1['Machine'] == machine) & (cookie_data_routes1['People'] == people)]
                            if not match.empty:
                                return match['MaterialCost/Qty_Reqd'].values[0],match['Labour&SetupCost/Qty_Reqd'].values[0], match['JobTime'].values[0]
                    return 0,0,0
                
                # Apply and calculate B_MaterialCost as the sum of matched costs from M1, M2, M3
                result_df[['B_MaterialCost', 'B_Labour&SetupCost']] =result_df['M1'].apply(lambda x: get_cost(x)[:2]).apply(pd.Series)
                result_df[['E_MaterialCost', 'E_Labour&SetupCost']] =result_df['M2'].apply(lambda x: get_cost(x)[:2]).apply(pd.Series)
                result_df[['R_MaterialCost', 'R_Labour&SetupCost']] =result_df['M3'].apply(lambda x: get_cost(x)[:2]).apply(pd.Series)
                result_df['B_Time(mins)'] =result_df['M1'].apply(lambda x: get_cost(x)[2])
                result_df['E_Time(mins)'] =result_df['M2'].apply(lambda x: get_cost(x)[2])
                result_df['R_Time(mins)'] =result_df['M3'].apply(lambda x: get_cost(x)[2])
                
                match1 = cookie_data_fixed1[cookie_data_fixed1['Stage'].str.contains("Mixing")][['Stage','MaterialCost/Qty_Reqd','Labour&SetupCost/Qty_Reqd']]
                
                result_df[['Dough_MaterialCost', 'Dough_Labour&SetupCost']]=match1[match1['Stage']=='Dough Mixing'][['MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd']].iloc[0].values
                if match1[match1['Stage']=='Colour Mixing (E)'].shape[0]==1:
                    result_df[['Color_E_MaterialCost', 'Color_E_Labour&SetupCost']]=match1[match1['Stage']=='Colour Mixing (E)'][['MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd']].iloc[0].values
                else: result_df[['Color_E_MaterialCost', 'Color_E_Labour&SetupCost']]=0,0
                if match1[match1['Stage']=='Colour Mixing (R)'].shape[0]==1:
                    result_df[['Color_R_MaterialCost', 'Color_R_Labour&SetupCost']]=match1[match1['Stage']=='Colour Mixing (R)'][['MaterialCost/Qty_Reqd', 'Labour&SetupCost/Qty_Reqd']].iloc[0].values
                else: result_df[['Color_R_MaterialCost', 'Color_R_Labour&SetupCost']]=0,0
                
                res=pd.concat([res,result_df], axis=0, ignore_index=True)
                
            res['MaterialCost']=res['B_MaterialCost'] + res['E_MaterialCost'] + res['R_MaterialCost'] + res['Dough_MaterialCost'] + res['Color_E_MaterialCost'] + res['Color_R_MaterialCost']
            res['Labour&SetupCost']=res['B_Labour&SetupCost'] + res['E_Labour&SetupCost'] + res['R_Labour&SetupCost'] + res['Dough_Labour&SetupCost'] + res['Color_E_Labour&SetupCost'] + res['Color_R_Labour&SetupCost']
            res['TotalCost']=res['MaterialCost'] + res['OrderQty']
            res['MaterialCost/Cookie']=res['MaterialCost'] / res['Labour&SetupCost']
            res['Labour&SetupCost/Cookie']=res['Labour&SetupCost'] / res['OrderQty']
            res['TotalCost/Cookie']=res['TotalCost'] / res['OrderQty']
            
            cookietray=40 #dummy number for cookies per tray
            res['#cookies/Rack']=40*cookietray
            res['MinsBake/Rack']= 40*cookietray*(res['B_Time(mins)']/res['OrderQty'] ) # 1 rack has 40 trays
            res['MinsEnr/Rack']=40*cookietray*(res['E_Time(mins)']/res['OrderQty'] )
            res['MinsDeco/Rack']=40*cookietray*(res['R_Time(mins)']/res['OrderQty'] )
            
            res['#ShiftsB/7.5hr']=(res['B_Time(mins)']/60)/7.5
            res['#ShiftsE/7.5hr']=(res['E_Time(mins)']/60)/7.5   
            res['#ShiftsR/7.5hr']=(res['R_Time(mins)']/60)/7.5
            
            
            res1=res[['Route', 'Route Cost', 'Route Job Time' ,'Name', 'OrderQty', 'MaterialCost' , 'Labour&SetupCost','TotalCost',
                      'MaterialCost/Cookie','Labour&SetupCost/Cookie','TotalCost/Cookie']]
            resTemp=res[['Route', 'Route Cost', 'Route Job Time' ,'B_Time(mins)','E_Time(mins)','R_Time(mins)','Name', 'OrderQty', 'MaterialCost' , 'Labour&SetupCost',
                      'TotalCost','MaterialCost/Cookie','Labour&SetupCost/Cookie','TotalCost/Cookie','#cookies/Rack','MinsBake/Rack','MinsEnr/Rack','MinsDeco/Rack',
                      '#ShiftsB/7.5hr','#ShiftsE/7.5hr','#ShiftsR/7.5hr']]
            st.session_state["res1"] = res1

            st.write(res1)
            st.write(resTemp) 
            #st.write(match1)
        
        
    if page=="Results":
        st.write("Results: Prices per complete route",st.session_state["res"])
        
        
            
# Run the app
if __name__ == "__main__":
    main()



