import tkinter as tk
from tkinter import messagebox,ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re
import datetime

# Configuration and constants
CONFIG={"sugar_limit":15,"sodium_limit":400,"fat_limit":20,"energy_limit":400}
WHO_DAILY={"energy":2000,"sugar":25,"sodium":2000,"fat":70}
CONDITIONS_LIST=["None","Diabetes","Hypertension","Heart Disease","Asthma","Kidney Disease","Obesity"]

ADDITIVES_DATA=[
    {"code":"102","name":"Tartrazine","risk":"HIGH","issues":"Hyperactivity, asthma"},
    {"code":"110","name":"Sunset Yellow FCF","risk":"HIGH","issues":"Hyperactivity, allergies, asthma"},
    {"code":"123","name":"Amaranth","risk":"HIGH","issues":"Possible carcinogen"},
    {"code":"124","name":"Ponceau 4R","risk":"HIGH","issues":"Hyperactivity, allergic reactions"},
    {"code":"127","name":"Erythrosine","risk":"HIGH","issues":"Thyroid problems, hyperactivity"},
    {"code":"128","name":"Red 2G","risk":"VERY HIGH","issues":"Carcinogenic"},
    {"code":"171","name":"Titanium Dioxide","risk":"HIGH","issues":"Possible carcinogen, banned in EU"},
    {"code":"211","name":"Sodium Benzoate","risk":"MEDIUM-HIGH","issues":"Benzene risk with Vit C"},
    {"code":"249","name":"Potassium Nitrite","risk":"HIGH","issues":"Forms carcinogenic nitrosamines"},
    {"code":"250","name":"Sodium Nitrite","risk":"HIGH","issues":"Carcinogenic nitrosamines"},
    {"code":"320","name":"BHA","risk":"HIGH","issues":"Possible carcinogen, hormone disruptor"},
    {"code":"951","name":"Aspartame","risk":"HIGH","issues":"Headaches, neurological effects"},
    {"code":"924","name":"Potassium Bromate","risk":"VERY HIGH","issues":"CARCINOGENIC - BANNED"},
    {"code":"927","name":"Azodicarbonamide","risk":"HIGH","issues":"Asthma, banned in EU"}
]
df_additives=pd.DataFrame(ADDITIVES_DATA)

# In-memory storage
session_users={}
session_logs=[]
current_active_user=None

# Functions
def add_user():
    global current_active_user
    name,age,weight,height,cond=u_name_box.get().strip(),u_age_box.get().strip(),u_weight_box.get().strip(),u_height_box.get().strip(),u_cond_box.get()
    if name and age and weight and height and cond:
        session_users[name]={"name":name,"age":age,"weight":weight,"height":height,"condition":cond}
        current_active_user=name 
        messagebox.showinfo("Success",f"Profile for {name} Saved. You can now analyze food.")
        u_name_box.delete(0,tk.END);u_age_box.delete(0,tk.END);u_weight_box.delete(0,tk.END);u_height_box.delete(0,tk.END)
        u_cond_box.current(0)
        show_history() 
    else:
        messagebox.showwarning("Warning","Please fill all user profile fields")

def analyze_and_add():
    if not current_active_user:
        messagebox.showwarning("No User","Please save a User Profile first.")
        return
        
    name=current_active_user
    ing=ing_box.get("1.0",tk.END).upper().strip()
    es,ss,ns,fs=energy_box.get(),sugar_box.get(),sodium_box.get(),fat_box.get()
    
    if ing and es and ss and ns and fs:
        try:
            energy,sugar,sodium,fat=float(es),float(ss),float(ns),float(fs)
            user_data=session_users.get(name)
            cond=user_data["condition"] if user_data else "None"
            
            score=10.0
            details=f"Analysis for: {name}\nMedical Condition: {cond}\n\nINGREDIENTS ANALYSIS:\n"
            codes_found=re.findall(r'(?:INS|E)\s*(\d+)',ing)
            found_mask=df_additives['code'].isin(codes_found)
            
            for _,row in df_additives[found_mask].iterrows():
                details+=f"• {row['name']} ({row['code']}): {row['issues']}\n"
                score-=2.0 if "HIGH" in row['risk'] else 1.0
            
            if not any(found_mask):
                details+="No high-risk additives found in database.\n"
                
            details+="\nNUTRITIONAL ANALYSIS:\n"
            if energy>CONFIG['energy_limit']:
                score-=1.0
                details+=f"! HIGH CALORIES: {energy} kcal\n"
            if sugar>CONFIG['sugar_limit']:
                score-=1.5
                details+=f"! HIGH SUGAR: {sugar}g\n"
                if cond=="Diabetes":
                    score-=2.0
                    details+="CRITICAL: Dangerous for Diabetes!\n"
            if sodium>CONFIG['sodium_limit']:
                score-=1.0
                details+=f"! HIGH SALT: {sodium}mg\n"
                if cond in ["Hypertension","Heart Disease"]:
                    score-=2.0
                    details+=f"CRITICAL: Dangerous for {cond}!\n"
            
            score=max(0.0,min(10.0,score))
            details+=f"\nFINAL SAFETY SCORE: {score}/10"
            
            now=datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            session_logs.append({"user_name":name,"score":score,"date":now})
            
            res_text.delete("1.0",tk.END);res_text.insert(tk.END,details)
            
            show_history()
            show_chart(energy,sugar,sodium,fat)
        except ValueError:
            messagebox.showerror("Error","Nutritional values must be numbers")
    else:
        messagebox.showwarning("Warning","Please fill all nutritional and ingredient fields")

def show_history():
    for row in tree.get_children():tree.delete(row)
    if not current_active_user:
        return
    filtered_data=[log for log in session_logs if log["user_name"]==current_active_user]
    for item in reversed(filtered_data):
        tree.insert("",tk.END,values=(item.get("user_name"),item.get("score"),item.get("date")))

def show_chart(e,s,n,f):
    for widget in chart_area.winfo_children():widget.destroy()
    fig,ax=plt.subplots(figsize=(5,4))
    categories=['Energy','Sugar','Sodium','Fat']
    food_pct_of_who=[(e/WHO_DAILY['energy'])*100,(s/WHO_DAILY['sugar'])*100,(n/WHO_DAILY['sodium'])*100,(f/WHO_DAILY['fat'])*100]
    x=np.arange(len(categories))
    ax.bar(x,food_pct_of_who,color='grey')
    ax.set_ylabel('% of WHO Daily Limit')
    ax.set_title('Packaged Food Nutrition vs WHO Guidelines')
    ax.set_xticks(x);ax.set_xticklabels(categories)
    ax.set_ylim(0,max(120,max(food_pct_of_who)+10))
    fig.tight_layout()
    FigureCanvasTkAgg(fig,master=chart_area).get_tk_widget().pack(fill=tk.BOTH,expand=True)

# GUI setup
root=tk.Tk()
root.title("Health and Food Analyzer")
root.geometry("1000x850")

tabs=ttk.Notebook(root)
tabs.pack(fill=tk.BOTH,expand=True,padx=10,pady=10)

tab_profile=tk.Frame(tabs);tab_analyzer=tk.Frame(tabs);tab_history=tk.Frame(tabs)
tabs.add(tab_profile,text=" User Profile ");tabs.add(tab_analyzer,text=" Food Analyzer ");tabs.add(tab_history,text=" History ")

# Tab 1: Profile section
tk.Label(tab_profile,text="User Name").grid(row=0,column=0,padx=20,pady=10,sticky="w")
u_name_box=tk.Entry(tab_profile,width=40);u_name_box.grid(row=0,column=1,padx=20,pady=10)
tk.Label(tab_profile,text="Age").grid(row=1,column=0,padx=20,pady=10,sticky="w")
u_age_box=tk.Entry(tab_profile,width=40);u_age_box.grid(row=1,column=1,padx=20,pady=10)
tk.Label(tab_profile,text="Weight (kg)").grid(row=2,column=0,padx=20,pady=10,sticky="w")
u_weight_box=tk.Entry(tab_profile,width=40);u_weight_box.grid(row=2,column=1,padx=20,pady=10)
tk.Label(tab_profile,text="Height (cm)").grid(row=3,column=0,padx=20,pady=10,sticky="w")
u_height_box=tk.Entry(tab_profile,width=40);u_height_box.grid(row=3,column=1,padx=20,pady=10)
tk.Label(tab_profile,text="Condition").grid(row=4,column=0,padx=20,pady=10,sticky="w")
u_cond_box=ttk.Combobox(tab_profile,values=CONDITIONS_LIST,state="readonly",width=37);u_cond_box.current(0);u_cond_box.grid(row=4,column=1,padx=20,pady=10)
tk.Button(tab_profile,text="Save User Profile",command=add_user).grid(row=5,column=1,pady=20,sticky="e")

# Tab 2: Analyzer section
analyzer_main=tk.Frame(tab_analyzer);analyzer_main.pack(fill=tk.BOTH,expand=True)
left_side=tk.Frame(analyzer_main);left_side.pack(side=tk.LEFT,fill=tk.BOTH,expand=True,padx=10)
tk.Label(left_side,text="Enter Packaged Food Nutrition Below:",font=("Arial",10,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=10)
tk.Label(left_side,text="Energy (kcal)").grid(row=1,column=0,sticky="w",pady=2)
energy_box=tk.Entry(left_side,width=30);energy_box.grid(row=1,column=1,pady=2)
tk.Label(left_side,text="Sugar (g)").grid(row=2,column=0,sticky="w",pady=2)
sugar_box=tk.Entry(left_side,width=30);sugar_box.grid(row=2,column=1,pady=2)
tk.Label(left_side,text="Sodium (mg)").grid(row=3,column=0,sticky="w",pady=2)
sodium_box=tk.Entry(left_side,width=30);sodium_box.grid(row=3,column=1,pady=2)
tk.Label(left_side,text="Fat (g)").grid(row=4,column=0,sticky="w",pady=2)
fat_box=tk.Entry(left_side,width=30);fat_box.grid(row=4,column=1,pady=2)
tk.Label(left_side,text="Ingredients").grid(row=5,column=0,sticky="nw",pady=2)
ing_box=tk.Text(left_side,height=4,width=25,wrap=tk.WORD);ing_box.grid(row=5,column=1,pady=2)
tk.Button(left_side,text="Analyze Food",command=analyze_and_add).grid(row=6,column=0,columnspan=2,pady=10)
res_text=tk.Text(left_side,height=12,width=45,wrap=tk.WORD);res_text.grid(row=8,column=0,columnspan=2,pady=5)
chart_area=tk.Frame(analyzer_main,width=400,height=400);chart_area.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True)

# Tab 3: History section
tree=ttk.Treeview(tab_history,columns=("User","Score","Date"),show="headings")
for col in ("User","Score","Date"):tree.heading(col,text=col);tree.column(col,width=150)
tree.pack(fill=tk.BOTH,expand=True,padx=10,pady=10)

show_history()
root.mainloop()
