from flask import Flask, render_template, request, jsonify

def F_gpm_to_m3_seg(gpm) :
    return gpm*0.00006309


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('flowComputing.html')


@app.route('/process_Cv', methods=['POST'])
def process_Cv():

    unit_flow = request.form['unit_flow']
    flow_in = request.form['flow']

    if unit_flow and flow_in:
            flow_out = F_gpm_to_m3_seg(flow_in)
            unit_out = 'm3_seg'
            console.log('enter in computation')
            return jsonify({'flow':flow_out, 'unit':unit_out})

    return jsonify({'error':'Missing data!'})



if __name__ == '__main__':
    app.run(debug=True)