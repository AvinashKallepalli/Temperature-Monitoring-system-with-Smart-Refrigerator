import mail, json, time, math, statistics
from boltiot import Email, Bolt
def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound]

mybolt = Bolt(mail.API_KEY, mail.DEVICE_ID)
mailer = Email(mail.MAILGUN_API_KEY, mail.SANDBOX_URL, mail.SENDER_EMAIL, mail.RECIPIENT_EMAIL)
history_data=[]

while True:
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error: " + str(data['value']))
        time.sleep(10)
        continue

    print ("This is the value "+data['value'])
    sensor_value=0
    try:
        sensor_value = int(data['value'])
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,mail.FRAME_SIZE,mail.MUL_FACTOR)
    if not bound:
        required_data_count=mail.FRAME_SIZE-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        if sensor_value > bound[0] :
            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "Someone has opened the fridge door " +str(sensor_value))
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        elif sensor_value < bound[1]:
            print("Making request to Mailgun to send an email")
            response = mailer.send_email("Alert", "Someone has closed the fridge door " +str(sensor_value))
            response_text = json.loads(response.text)
            print("Response received from Mailgun is: " + str(response_text['message']))
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)
    time.sleep(10)
