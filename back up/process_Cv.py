import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
import numpy as np

from fluids import *
from scipy.constants import *
from fluids.control_valve import size_control_valve_l
from thermo.chemical import Chemical

def F_to_m3_seg(data, input, rho) :
    input = 'flow_'+input

 
    if data['flow_unit'] == "gpm" :
        return float(data[input])*0.227/3600
    #if mass flow units: ton/hr 
    if data['flow_unit'] == "ton_hr" : 
        return float(data[input])/rho/3600
    if data['flow_unit'] == "m3_hr" :
        return float(data[input])/3600
    if data['flow_unit'] == "m3_seg" :
        return float(data[input])

def P_to_Pascal(data, input) :
    input1 = 'P1_'+input
    input2 = 'P2_'+input   
    if data['press_unit'] == "psi" :
        return float(data[input1])* 6894.75728 , float(data[input2])* 6894.75728
    if data['press_unit'] == "bar" :
        return float(data[input1])* 100000 , float(data[input2])* 100000
    if data['press_unit'] == "Pascal" :
        return float(data[input1]) , float(data[input2])
    if data['press_unit'] == "kPascal" :
        return float(data[input1])*1000 , float(data[input2])*1000

def T_to_K(data, input) :
    input = 'temp_'+input
    if data['temp_unit'] == "C":
        return float(data[input])+273.15
    if data['temp_unit'] == "F":
        return (float(data[input]) - 32)*5/9 + 273.15
    if data['temp_unit'] == "K":
        return float(data[input]) 

def D_to_meter(data, d, pipe_unit) :
    if pipe_unit == "in" :
        return float(data['inletD'])*0.0254 , float(data['outletD'])*0.0254 , d*0.0254
    if pipe_unit == "mm" :
        return float(data['inletD'])*0.001 , float(data['outletD'])*0.001 , d*0.001
    if pipe_unit == "m" :
        return float(data['inletD']) , float(data['outletD']) , d

def in_to_mm(value) :
    return value*25.40

#global for valve dataframe and Nominal Pipe Sizes 
df = pd.DataFrame()
data_return = {}
pipe_table = pd.read_csv('pipe_dimensions.csv')
pipe_table.set_index('NPS_in') 

app = Flask(__name__)
# app.run(host = '127.0.0.1', port=5000)

@app.route('/')
#load valve data and populate menu drop down for valve selection and inject on flowComputing.html 
#every valve is a csv file 
def index():
    global pipe_table
    #all NPS available for selection 

 
    NPS_in = dict( pipe_table['NPS_in'])
    OD_in = dict(pipe_table['OD_in'])
    # print(jsonify({'NPS_in': 4}))

    print(dict(NPS_in))
    datos = [{'name' : 'Masoneilan 21000 Series FTC LINEAR TRIM',
              'value': 'Masoneilan_21000_FTC_Linear_Trim.csv'},
             {'name' : 'Masoneilan 21000 Series FTC EQUAL PERCENT',
              'value': 'Masoneilan_21000_FTC_Equal_Percent.csv' }           
              ]
    return render_template('flowComputing.html', data=datos, pipe_info=NPS_in, pipe_OD = OD_in )

#a change was made on NPS Inlet and output to populate select options for schedule
@app.route('/pipe', methods=['POST'])
def pipe():
    global pipe_table
    json_data = request.form
    D1 = float(json_data['OD_in'])
    sch_for_D1 = pipe_table[ pipe_table['OD_in'] == D1]

   
    print('you have selected NPS_in for Inlet:', D1)
    print('All Schedule possible to return for this: ')
    print(sch_for_D1)
    sch_for_D1 = sch_for_D1.loc[:,sch_for_D1.notnull().all()]
    sch_for_D1 = sch_for_D1.set_index('OD_in')
    #show only columns with actual values
    # print(sch_for_D1.iloc[0,1:])

    # print(sch_for_D1.iloc[0, '80'])


    sched_return = sch_for_D1.to_json(orient = "records")
    print(sched_return)


    # for col in sch_for_D1 : 
    #    sched_return.  sch_for_D1[col]

    # print("Dictionary to pass: ", sched_return)

  
    return jsonify(sched_return)


#a change was made on Valve selection and rated Size and Rated Cv needs to be check
@app.route('/valve', methods=['POST'])
def valve():
    json_data = request.form
    print('Entering in valve , receiving: ', json_data['model'])
    global df
    df = pd.read_csv(json_data['model']) #valve model selected / ready to extract valve size 
    df.set_index('Valve_Size_in')
    print(df.head())

    valve_size = df['Valve_Size_in'].unique()
    valve_size = np.delete(valve_size, [0]).tolist()  #remove 0 size *** first row of every table is for FL and 0 size, diameter, travel 
    return jsonify({'lista': valve_size})

@app.route('/valve_sizing', methods=['POST'])
def valve_sizing():
    global data_return
    global df
    json_data = request.form
    pipe_unit = "in"  #NPS in by default 
    print('server has received data from Valve Sizing **********************')
    print(json_data['ratedCv'])
    
    line = json_data['Cv_required'].replace("[","")
    line = line.replace("]","")
    print(line)

    Cv_required = np.fromstring(line, dtype=float, sep=',')
    print(Cv_required[0])
    #  from table get proper row where to iterate for RatedCv calculations
    table = df[df['Valve_Size_in'] == float(json_data['valve_size'])]
    selected = table.loc[ table['100%'] == float(json_data['ratedCv']) ]

    array_ratedCv = np.array(selected.iloc[0].values[7:17], dtype=np.float)
    array_FL = np.array(df.iloc[0].values[7:17], dtype=np.float)
    d_valve_orifice = selected.iloc[0][3]
    array_PTravel = [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0,90.0,100.0]
    # Cv_required = float(json_data['Cv_required'][0])

    # % of Travel & % Cv interpolation for 3 cases if exists or at least Op in 0
    PTravel = [0.0, 0.0, 0.0]
    P_Cv = [0.0, 0.0, 0.0]
    FL_Cv = [0.0, 0.0, 0.0]
    CavIndex = [-1.0, -1.0, -1.0]

    PTravel[0] = round(np.interp(Cv_required[0], array_ratedCv, array_PTravel ),2)
    P_Cv[0] =  round((Cv_required[0] / array_ratedCv[-1])*100, 2)
    FL_Cv[0] = round(np.interp(Cv_required[0], array_ratedCv, array_FL),2)

    #New calculations for Cv now this time with D1, D2 and d, FL 
    valid_data = True
    min_exist = (json_data['check_Min'] == 'true')
    max_exist = (json_data['check_Max'] =='true')

    fig = plt.figure()
    ax = fig.add_subplot(211)
    bx = fig.add_subplot(212)

    if valid_data:
        P1 , P2 =  P_to_Pascal(json_data, 'Op')
        T = T_to_K(json_data, 'Op')
        print('OD Pipe & Valve check (in): ')
        print(json_data['inletD'])
        print(json_data['outletD'])
        print(json_data['valve_size'])


        D1 , D2, d = D_to_meter(json_data, d_valve_orifice, pipe_unit)
        print(d*1000)
        liquid = Chemical(json_data['liquid'], P=P1, T=T)
        rho = liquid.rho
        Psat = liquid.Psat
        Pc = liquid.Pc
        mu = liquid.mu
        F = F_to_m3_seg(json_data, 'Op', rho/1000)
        FL = FL_Cv[0]

        for item in array_FL :
            print('FL from array: ', item)
#
        #Sizing calculation considering D, Valve (d) and FL - Fd = 1 FLow to Close
        sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, D1=D1, D2=D2,
                         d=d, FL=0.8, Fd=1, full_output=True)

                        
        print('All data Output: ', sizing)
        Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 2)
        Cv_Op = round(Kv_to_Cv(sizing['Kv']), 4)
        print('Cv Op / con d / D1 / D2: ', Cv_Op, d*1000, D1*1000, D2*1000 )
        # print('Cv Req: ', Cv_required[0])
        print('Cavitation index: ', Cav_index)


        Cv_required[0] = Cv_Op
        CavIndex[0] = Cav_index
        PTravel[0] = round(np.interp(Cv_required[0], array_ratedCv, array_PTravel ),2)
        P_Cv[0] =  round((Cv_required[0] / array_ratedCv[-1])*100, 2)
        FL_Cv[0] = round(np.interp(Cv_required[0], array_ratedCv, array_FL),4)

        # new calculation this time corrected with FL from valve 
        # sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, D1=D1, D2=D2,
        #                  d=d, FL=0.9, Fd=1, full_output=True)
        
        Cv_Op = round(Kv_to_Cv(sizing['Kv']), 4)
        print('Cv con FL: ', Cv_Op, FL_Cv[0] )



        ax.scatter(PTravel[0], Cv_required[0], color='red', marker='+', linewidth=5)
        bx.scatter(PTravel[0], FL_Cv[0], color='red', marker='+', linewidth=5)


    # if (Cv_required[1] != 0) :
    if (min_exist)  :
        P1 , P2 =  P_to_Pascal(json_data, 'Min')
        T = T_to_K(json_data, 'Min')
        D1 , D2, d = D_to_meter(json_data, d_valve_orifice, pipe_unit)
        liquid = Chemical(json_data['liquid'], P=P1, T=T)
        rho = liquid.rho
        Psat = liquid.Psat
        Pc = liquid.Pc
        mu = liquid.mu
        F = F_to_m3_seg(json_data, 'Min', rho/1000)

        PTravel[1] = round(np.interp(Cv_required[1], array_ratedCv, array_PTravel ),2)
        P_Cv[1] =  round((Cv_required[1] / array_ratedCv[-1])*100, 2)
        FL_Cv[1] = round(np.interp(Cv_required[1], array_ratedCv, array_FL),2)

        FL = FL_Cv[1]

        #Sizing calculation considering D, Valve and FL
        sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, D1=D1, D2=D2,
                         d=d, FL=0.9, Fd=1, full_output=True)
        Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 2)
        Cv_Min = round(Kv_to_Cv(sizing['Kv']), 4)
        print('Cv Min: ', Cv_Min )
        print('Cavitation index: ', Cav_index)
        Cv_required[1] = Cv_Min
        CavIndex[1] = Cav_index
        PTravel[1] = round(np.interp(Cv_required[1], array_ratedCv, array_PTravel ),2)
        P_Cv[1] =  round((Cv_required[1] / array_ratedCv[-1])*100, 2)
        FL_Cv[1] = round(np.interp(Cv_required[1], array_ratedCv, array_FL),2)

        ax.scatter(PTravel[1], Cv_required[1], color='red', marker='+', linewidth=5)
        bx.scatter(PTravel[1], FL_Cv[1], color='red', marker='+', linewidth=5)



    # if (Cv_required[2] != 0) :
    if (max_exist) :
        P1 , P2 =  P_to_Pascal(json_data, 'Max')
        T = T_to_K(json_data, 'Max')
        D1 , D2, d = D_to_meter(json_data, d_valve_orifice, pipe_unit)
        liquid = Chemical(json_data['liquid'], P=P1, T=T)
        rho = liquid.rho
        Psat = liquid.Psat
        Pc = liquid.Pc
        mu = liquid.mu
        F = F_to_m3_seg(json_data, 'Max', rho/1000)

        PTravel[2] = round(np.interp(Cv_required[2], array_ratedCv, array_PTravel ),2)
        P_Cv[2] =  round((Cv_required[2] / array_ratedCv[-1])*100, 2)
        FL_Cv[2] = round(np.interp(Cv_required[2], array_ratedCv, array_FL),2)
        FL = FL_Cv[2]

        #Sizing calculation considering D, Valve and FL
        sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, D1=D1, D2=D2,
                         d=d, FL=0.9, Fd=1, full_output=True)
        Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 2)
        Cv_Max = round(Kv_to_Cv(sizing['Kv']), 4)
        print('Cv Max: ', Cv_Max )
        print('Cavitation index: ', Cav_index)
        Cv_required[2] = Cv_Max
        CavIndex[2] = Cav_index
        PTravel[2] = round(np.interp(Cv_required[2], array_ratedCv, array_PTravel ),2)
        P_Cv[2] =  round((Cv_required[2] / array_ratedCv[-1])*100, 2)
        FL_Cv[2] = round(np.interp(Cv_required[2], array_ratedCv, array_FL),2)

        ax.scatter(PTravel[2], Cv_required[2], color='red', marker='+', linewidth=5)
        bx.scatter(PTravel[2], FL_Cv[2], color='red', marker='+', linewidth=5)

    # percentage_to_plot = np.delete(PTravel, 0.0)
    # FL_to_plot = np.delete(FL_Cv, 0.0)
 

    # Display Plot Flow Valve & procces data 
    bx.plot(array_PTravel, array_FL, color='green', linewidth=1)
    ax.plot(array_PTravel, array_ratedCv, color='black', linewidth=1)
    
    ax.set_ylabel('Rated Cv')
    bx.set_xlabel('Percent of Travel - %')
    bx.set_ylabel('FL')

    plt.savefig('./static/docs/grafico.png')
    plt.close()
    
    

    return jsonify({
                    'CvOp' : Cv_required[0],
                    'CvMin' : Cv_required[1] if (Cv_required[1] != 0) else '-',
                    'CvMax' : Cv_required[2] if (Cv_required[1] != 0) else '-',
                    'CavIndexOp' : CavIndex[0],
                    'CavIndexMin' : CavIndex[1] if (CavIndex[1] != -1.0) else '-',
                    'CavIndexMax' : CavIndex[2] if (CavIndex[2] != -1.0) else '-',
                    'travelOp' : PTravel[0],
                    'travelMin' : PTravel[1] if (Cv_required[1] != 0) else '-', 
                    'travelMax' : PTravel[2] if (Cv_required[2] != 0) else '-',
                    'percentageCvOp' : P_Cv[0],
                    'percentageCvMin' : P_Cv[1] if (Cv_required[1] != 0) else '-', 
                    'percentageCvMax' : P_Cv[2] if (Cv_required[2] != 0) else '-',
                    'FLOp'              : FL_Cv[0],
                    'FLMin' : FL_Cv[1] if (Cv_required[1] != 0) else '-', 
                    'FLMax' : FL_Cv[2] if (Cv_required[2] != 0) else '-'  
                    })



@app.route('/rated_Cv', methods=['POST'])
def rated_Cv():
    global df  #master data for Valve Model selected global 
    json_data = request.form
    size = float(json_data['size'])
    # print(df['Valve_Size_in'] == size)
    size_selected = df[df['Valve_Size_in'] == size]
    print(type(size_selected))
    #return in json format every row with valve size 
    
    global data_return
    data_return = {}
    data_return['FL'] = df.loc[0,'10%':'100%'].tolist()

    for row in size_selected :
        data_return[row] = size_selected[row].tolist()
    return ( jsonify(data_return))



@app.route('/process', methods=['POST'])
def process():

# loading variables from JSON
    json_data = request.form
    pipe_unit = "in"  #NPS in by default 
# Diameter in meters (Pipe ID) Pressure in Pascal , Flow in m3-seg and T in Kelvin for Cv computation
    
    valid_data = True

    min_exist = (json_data['check_Min'] == 'true')
    max_exist = (json_data['check_Max'] =='true')

    if valid_data:
        P1 , P2 =  P_to_Pascal(json_data, 'Op')
        T = T_to_K(json_data, 'Op')

        # liquid = Chemical(json_data['liquid'], P=(P1+P2)/2, T=T)  #check P Max ??
        liquid = Chemical(json_data['liquid'], P=P1, T=T)
        rho = liquid.rho
        Psat = liquid.Psat
        Pc = liquid.Pc
        mu = liquid.mu
        F = F_to_m3_seg(json_data, 'Op', rho/1000)

        result = { 'rhoOp' : round(liquid.rho/1000,4),
                   'PsatOp' : round(liquid.Psat*0.000145,2),
                   'PcOp' : round(liquid.Pc*0.000145,2),
                   'muOp' : round(liquid.mu*1000,4),
                }

        sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, Fd=1, full_output=True)
        Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 2)
        Cv_Op = round(Kv_to_Cv(sizing['Kv']), 4)
        result['Cv_Op'] = Cv_Op
        result['CavIndexOp'] = Cav_index
        #Critical FL
        FL_Pvc = ((P1-P2)/(P1 - (0.96-0.28*(Psat/Pc)**0.5)))**0.5
        result['FL_Pvc_Op'] = round(FL_Pvc,4)
        # print('Cavitation index: ', Cav_index)
        # print('Rev: ', sizing['Rev'])
        # print('Laminar: ', sizing['laminar'])


        # print('Calculation FL with Pvc: ', FL_Pvc)

    if min_exist :
            print('Tambien debo calcular y retornar para Min')
            P1 , P2 =  P_to_Pascal(json_data, 'Min')
            T = T_to_K(json_data, 'Min')
            print('Ya tengo la data en formato ... para los calculos')
            liquid = Chemical(json_data['liquid'], P=P1, T=T)
            rho = liquid.rho
            Psat = liquid.Psat
            Pc = liquid.Pc
            mu = liquid.mu
            F = F_to_m3_seg(json_data, 'Min', rho/1000)

            result['rhoMin'] = round(liquid.rho/1000,4)
            result['PsatMin'] = round(liquid.Psat*0.000145,2)
            result['PcMin'] = round(liquid.Pc*0.000145,2)
            result['muMin'] = round(liquid.mu*1000,4)
                

            sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, Fd=1, full_output=True)
            Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 2)
            Cv_Min = round(Kv_to_Cv(sizing['Kv']), 4)
            result['Cv_Min'] = Cv_Min
            result['CavIndexMin'] = Cav_index
            #Critical FL
            FL_Pvc = ((P1-P2)/(P1 - (0.96-0.28*(Psat/Pc)**0.5)))**0.5
            result['FL_Pvc_Min'] = round(FL_Pvc,4)
    else :
            print('No hace falta preparar data for Min')



    if  max_exist:
            print('Tambien debo calcular y retornar para Max')
            P1 , P2 =  P_to_Pascal(json_data, 'Max')
            T = T_to_K(json_data, 'Max')
            print('Ya tengo la data en formato ... para los calculos')
            liquid = Chemical(json_data['liquid'], P=P1, T=T)
            rho = liquid.rho
            Psat = liquid.Psat
            Pc = liquid.Pc
            mu = liquid.mu
            F = F_to_m3_seg(json_data, 'Max',rho/1000)

            result['rhoMax'] = round(liquid.rho/1000,4)
            result['PsatMax'] = round(liquid.Psat*0.000145,2)
            result['PcMax'] = round(liquid.Pc*0.000145,2)
            result['muMax'] = round(liquid.mu*1000,4)
                
            sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, Fd=1, full_output=True)
            Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 2)
            Cv_Max = round(Kv_to_Cv(sizing['Kv']), 4)
            result['Cv_Max'] = Cv_Max
            result['CavIndexMax'] = Cav_index
            #Critical FL
            FL_Pvc = ((P1-P2)/(P1 - (0.96-0.28*(Psat/Pc)**0.5)))**0.5
            result['FL_Pvc_Max'] = round(FL_Pvc,4)
    else :
            print('No hace falta preparar data for Max')



    return jsonify(result)
        # return jsonify({'Cv':Cv_Op,
        #                 'Cav_index':Cav_index,
        #                 'rho' : round(liquid.rho/1000,4),
        #                 'Psat' : round(liquid.Psat*0.000145,2),
        #                 'Pc' : round(liquid.Pc*0.000145,2),
        #                 'mu' : round(liquid.mu*1000,4),
        #                 'Cv_min' : 
        #                 })

    return jsonify({'error':'Missing data!'})

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host = '192.168.0.102', port=5000)