import matplotlib
# matplotlib.use('Agg')
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
    if data['press_unit'] == "kPascal" :
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

def D_to_meter(data, pipe_unit) :
    if pipe_unit == "in" :
        return float(data['inletD'])*0.0254 , float(data['outletD'])*0.0254 , float(data['valve_size'])*0.0254
    if pipe_unit == "mm" :
        return float(data['inletD'])*0.001 , float(data['outletD'])*0.001 , float(data['valve_size'])*0.001
    if pipe_unit == "m" :
        return float(data['inletD']) , float(data['outletD']) , float(data['valve_size'])

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
    array_PTravel = [10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0,90.0,100.0]
    # Cv_required = float(json_data['Cv_required'][0])

    # % of Travel & % Cv interpolation for 3 cases if exists or at least Op in 0
    PTravel = [0.0, 0.0, 0.0]
    P_Cv = [0.0, 0.0, 0.0]
    FL_Cv = [0.0, 0.0, 0.0]

    PTravel[0] = round(np.interp(Cv_required[0], array_ratedCv, array_PTravel ),2)
    P_Cv[0] =  round((Cv_required[0] / array_ratedCv[-1])*100, 2)
    FL_Cv[0] = round(np.interp(Cv_required[0], array_ratedCv, array_FL),2)
    print(array_FL)
    print(FL_Cv[0])

    # print('Op % Travel: ' , PTravel[0])
    # print('Op % Cv: ', P_FL[0])


    #New calculations for Cv now this time with D1, D2 and d, FL 
    valid_data = True
    min_exist = (json_data['check_Min'] == 'true')
    max_exist = (json_data['check_Max'] =='true')

    if valid_data:
        P1 , P2 =  P_to_Pascal(json_data, 'Op')
        T = T_to_K(json_data, 'Op')
        D1 , D2, d = D_to_meter(json_data, pipe_unit)
        liquid = Chemical(json_data['liquid'], P=P1, T=T)
        rho = liquid.rho
        Psat = liquid.Psat
        Pc = liquid.Pc
        mu = liquid.mu
        F = F_to_m3_seg(json_data, 'Op', rho/1000)
        FL = FL_Cv[0]

        print("Ready to call valve_sizing with Diameters values: ")
        print("P1 ", P1," P2 ",P2, " T ", T, " D1 ", D1, " D2 ",D2, " d ",d, " F ", F)
        #Sizing calculation considering D, Valve and FL
        sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, D1=D1, D2=D2,
                         d=d, FL=FL, Fd=1, full_output=True)
        Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 4)
        Cv_Op = round(Kv_to_Cv(sizing['Kv']), 4)
        print('Cv: ', Cv_Op )
        print('Cavitation index: ', Cav_index)
        Cv_required[0] = Cv_Op
        PTravel[0] = round(np.interp(Cv_required[0], array_ratedCv, array_PTravel ),2)
        P_Cv[0] =  round((Cv_required[0] / array_ratedCv[-1])*100, 2)
        FL_Cv[0] = round(np.interp(Cv_required[0], array_ratedCv, array_FL),2)


    if (Cv_required[1] != 0) :
        PTravel[1] = round(np.interp(Cv_required[1], array_ratedCv, array_PTravel ),2)
        P_Cv[1] =  round((Cv_required[1] / array_ratedCv[-1])*100, 2)
        # print('Min % Travel: ' , PTravel[1])
        # print('Min % Cv: ', P_FL[1])

    if (Cv_required[2] != 0) :
        PTravel[2] = round(np.interp(Cv_required[2], array_ratedCv, array_PTravel ),2)
        P_Cv[2] =  round((Cv_required[2] / array_ratedCv[-1])*100, 2)
        # print('Max % Travel: ' , PTravel[2])
        # print('Max % Cv: ', P_FL[2])

    # Display Plot Flow Valve & procces data 
    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax.plot(array_PTravel, array_ratedCv, color='black', linewidth=1)
    ax.scatter(PTravel, Cv_required, color='red', marker='+', linewidth=5)
    bx = fig.add_subplot(212)
    bx.plot(array_PTravel, array_FL, color='green', linewidth=1)
    # bx.scatter(P_FL, array_ratedCv, color='red', marker='+', linewidth=5)
    ax.set_ylabel('Rated Cv')
    bx.set_xlabel('Percent of Travel - %')
    bx.set_ylabel('FL')
    # ax.title(json_data['valve_model'])
    print(type(json_data['valve_model']))
    # plt.show()
    plt.savefig('./static/docs/grafico.png')
    plt.close()
    
   # print(ratedCv)
    # print(array_ratedCv)
    # print(array_PTravel)

    # % of Cv 

    return jsonify({
                    'CvOp' : Cv_required[0],
                    'CvMin' : Cv_required[1] if (Cv_required[1] != 0) else '-',
                    'CvMax' : Cv_required[2] if (Cv_required[1] != 0) else '-',
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

        result = { 'rho' : round(liquid.rho/1000,4),
                   'Psat' : round(liquid.Psat*0.000145,2),
                   'Pc' : round(liquid.Pc*0.000145,2),
                   'mu' : round(liquid.mu*1000,4),
                }

        sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, Fd=1, full_output=True)
        Cav_index = round(cavitation_index(P1=P1, P2=P2, Psat=Psat), 4)
        Cv_Op = round(Kv_to_Cv(sizing['Kv']), 4)
        print('Cv: ', Cv_Op )
        result['Cv_Op'] = Cv_Op
        print('Cavitation index: ', Cav_index)
        print('Rev: ', sizing['Rev'])
        print('Laminar: ', sizing['laminar'])


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
            sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, Fd=1, full_output=True)
            Cv_Min = round(Kv_to_Cv(sizing['Kv']), 4)
            result['Cv_Min'] = Cv_Min
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

            sizing = size_control_valve_l(rho, Psat, Pc, mu, P1, P2, F, Fd=1, full_output=True)
            Cv_Max = round(Kv_to_Cv(sizing['Kv']), 4)
            result['Cv_Max'] = Cv_Max
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
    # app.run(host = '192.168.0.106', port=5000)