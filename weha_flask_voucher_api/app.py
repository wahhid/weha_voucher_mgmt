from flask import Flask, request
app = Flask(__name__)


@app.route('/vs', methods=['GET', 'POST'])
def vs():
    if request.method == 'POST':
        print(request.form.get('date'))
        #print(request.form['time'])
        #print(request.form.get("receipt_number", False))
        #print(request.form['t_id'])
        #print(request.form['store_id'])
        #print(request.form['member_id'])
        #print(request.form['voucher_ean'])
    return "Received"

if __name__ == '__main__':
    app.run(debug=True)