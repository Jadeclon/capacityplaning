# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 08:32:07 2021

@author: jadec
"""

# streamlit run "C:/Users/jadec/OneDrive/Workspaces/pythonWorkspace/productionPlaning3.py"

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime
import datetime as dt
import random



# =============================================================================
# Global Variables
# =============================================================================
repeat = [1,1,1]

allBGs = []
logList = []

bg_times = pd.DataFrame([[15,10,20],[10, 15, 20],[20, 5, 30]], columns=["Drehen", "Fräsen", "Schleifen"])



# =============================================================================
# Logged die Daten
# =============================================================================
def log(msg):
    # timestamp = datetime.now()
    # msg = str(timestamp) + ' ' + msg
    # print(msg)
    logList.append(msg)




if 'df2' not in st.session_state:
    df2 = pd.DataFrame()
    st.session_state.df2 = pd.DataFrame()
    print("> df2 neu erstellt!")
else:
    df2 = st.session_state.df2
    print("> df2 geladen!")
    print(df2)
    
    
    
schichtbeginn = st.sidebar.time_input('Schichtbeginn', dt.time(8,0))
schichtende = st.sidebar.time_input('Schichtende', dt.time(16,0))
st.sidebar.markdown('\n')




# =============================================================================
# Header
# =============================================================================
st.write("""
# Interaktiver Kapazitätsabgleich
""")



# =============================================================================
# Baugruppen Klasse
# =============================================================================
class BG:
    
    def __init__(self, bgType):
        self.bgType = bgType
    
    bgType = 99
    endTimes = pd.DataFrame( np.array([[dt.datetime(2019, 4, 13, schichtbeginn.hour, schichtbeginn.minute), dt.datetime(2019, 4, 13, schichtbeginn.hour, schichtbeginn.minute), dt.datetime(2019, 4, 13, schichtbeginn.hour, schichtbeginn.minute)]]), columns=['Drehen', 'Fräsen', 'Schleifen'])
# =============================================================================


def addMinutes(time, minutes):
    if (time.minute + minutes) < 60:
        time = dt.datetime(2019, 4, 13, time.hour, (time.minute+minutes))
    else:
        if time.hour+1 < schichtende.hour:
            newMinutes = minutes-(60-time.minute)
            time = dt.datetime(2019, 4, 13, (time.hour+1), newMinutes)
        else:
            raise Exception('Soviel kann an einem Tag nicht produziert werden!')
    return time




# =============================================================================
# Fügt einen Arbeitsvorgang hinzu
# =============================================================================
def addRow(machine, id1):
    global df2
    bgType = int(id1[2:])-1

    bg = BG(bgType)

    if machine == 'Drehen':
        allBGs.append(bg)
        bgId = id1+'_'+str(random.randint(0,9999))
        start = bg.endTimes.loc[0][machine]
    elif machine == 'Fräsen':
        start = bg.endTimes.loc[0]['Drehen']
        bgId = df2.loc[len(df2)-1]['id']
        if allBGs[(len(allBGs)-1)].endTimes.loc[0][machine] > start:
            start = allBGs[(len(allBGs)-1)].endTimes.loc[0][machine] 
    elif machine == 'Schleifen':
        start = bg.endTimes.loc[0]['Fräsen']
        bgId = df2.loc[len(df2)-1]['id']
        if allBGs[(len(allBGs)-1)].endTimes.loc[0][machine] > start:
            start = allBGs[(len(allBGs)-1)].endTimes.loc[0][machine] 
        
    log(bgId)

    try:
        bg.endTimes.loc[0][machine] = addMinutes(start, bg_times.loc[bgType][machine])
    except:
        raise Exception('Soviel kann an einem Tag nicht produziert werden!')
        
    df3 = pd.DataFrame(np.array([[machine, start, bg.endTimes.loc[0][machine], bgId]]), columns=['machine', 'start', 'end', 'id'])
    df2 = df2.append( df3, ignore_index=True )
    log("AddRow: " + id1 + " " + machine + " | Start: " + str(start) + " | Ende: " + str(bg.endTimes.loc[0][machine]) + "\n")
    if machine == 'Schleifen':
        log("===============================================")



figPlot = st.empty()


# =============================================================================
# Aktualisiert das Diagramm
# =============================================================================
def updateFig():
    global fig
    fig = px.timeline(df2, x_start="start", x_end="end", y="machine", color='id', height=500, width=900, category_orders={'machine': ['Drehen', 'Fräsen', 'Schleifen']})
    
    figPlot.write(fig)

    st.session_state.df2 = df2



# =============================================================================
# Platzhalter
# =============================================================================
logText = st.empty()
error = st.empty()



# =============================================================================
# Startet die Berechnung
# =============================================================================
def startProgram(bg, repeat):
    
    # allBGs = []
    log('Starting program with ' + str(repeat))

    for i in range(repeat):
        # bg = random.randint(0,2)
        bgId = "BG" + str((bg+1))
        
        try:
            addRow("Drehen", bgId)
            addRow("Fräsen", bgId)
            addRow("Schleifen", bgId)
        except:
            error.error('Soviel kann in der Schicht nicht produziert werden!')
            break
        
    updateFig()
    # logText.write(logList)
        

        
# =============================================================================
# Zeigt an wie viel Leerlaufzeit es gab
# =============================================================================
pauseTextInsgesamt = st.empty()
pauseText1 = st.empty()
pauseText2 = st.empty()
pauseText3 = st.empty()
pause = 0
        
def brechneLeerlaufInsgesamt():
    global pause
    count = 0
    for i in range(len(df2)-1):
        if len(df2) > (i+3):
            log(df2.loc[i]['machine'] + ' | ' + str(df2.loc[i]['end']) + ' | ' + str(df2.loc[i+3]['start']))
            if df2.loc[i]['end'] == df2.loc[i+3]['start']:
                log('Same')
            else:
                if df2.loc[i]['end'].hour == df2.loc[i+3]['start'].hour:
                    leerzeit = df2.loc[i+3]['start'].minute - df2.loc[i]['end'].minute
                    pause += leerzeit
                    log('> Es werden ' + str(leerzeit) + ' Minuten Leerzeit notiert.')
                else:
                    leerzeit = (60 - df2.loc[i]['end'].minute) + df2.loc[i+3]['start'].minute
                    pause += leerzeit
                    # log('> Oh ein Stundenwechsel! Wir müssen etwas dagegen tun!')
                    log('> Es werden ' + str(leerzeit) + ' Minuten Leerzeit notiert.')
     
    log('\nDie Maschinen mussten insgesamt ' + str(pause) + ' Minuten zwischen den Bearbeitungen warten:')
    pauseTextInsgesamt.write('\n**Die Maschinen mussten insgesamt ' + str(pause) + ' Minuten zwischen den Bearbeitungen warten:**')
    
    
    
    
def berechneLeerlaufVon(machine):
    leerzeit = 0
    for i in range(len(df2)):    
        if len(df2) > (i+3):
            if df2.loc[i]['machine'] == machine:
                log(machine + ' | Ende: ' + str(df2.loc[i]['end']) + ' | ' + str(df2.loc[i+3]['start']))
                if df2.loc[i]['end'] == df2.loc[i+3]['start']:
                    log('Same')
                else:
                    if df2.loc[i]['end'].hour == df2.loc[i+3]['start'].hour:
                        leerzeit += df2.loc[i+3]['start'].minute - df2.loc[i]['end'].minute
                        log('> Es werden ' + str(leerzeit) + ' Minuten Leerzeit notiert.')
                    else:
                        leerzeit += (60 - df2.loc[i]['end'].minute) + df2.loc[i+3]['start'].minute
                        log('> Es werden ' + str(leerzeit) + ' Minuten Leerzeit notiert.')
                
    
    if machine == 'Drehen':
        pauseText1.write('\n>' + str(leerzeit) + ' Minuten an der ' + machine[:-2] + 'maschine.')
    if machine == 'Fräsen':
        pauseText2.write('\n>' + str(leerzeit) + ' Minuten an der ' + machine[:-2] + 'maschine.')
    if machine == 'Schleifen':
        pauseText3.write('\n>' + str(leerzeit) + ' Minuten an der ' + machine[:-2] + 'maschine.')


# =============================================================================
# Startet das Programm und ermittelt nur die Leerlaufzeit wenn mehr als eine Baugruppe produziert wird.
# =============================================================================

def reset():
    global df2
    df2 = pd.DataFrame()
    st.session_state.df2 = pd.DataFrame()


st.session_state.countB1 = 0
st.session_state.countB2 = 0
st.session_state.countB3 = 0


st.session_state.countB1 = st.sidebar.number_input('Wie viele B1 Bauteile möchten Sie produzieren?', min_value=1, step=1, value=repeat[0])
st.session_state.countB2 = st.sidebar.number_input('Wie viele B2 Bauteile möchten Sie produzieren?', min_value=1, step=1, value=repeat[1])
st.session_state.countB3 = st.sidebar.number_input('Wie viele B3 Bauteile möchten Sie produzieren?', min_value=1, step=1, value=repeat[2])
# st.sidebar.button("Reset", on_click=reset())
reset()


startProgram(0, int(st.session_state.countB1))
startProgram(1, int(st.session_state.countB2))
startProgram(2, int(st.session_state.countB3))

berechneLeerlaufVon('Drehen')
berechneLeerlaufVon('Fräsen')
berechneLeerlaufVon('Schleifen')
    
brechneLeerlaufInsgesamt()














