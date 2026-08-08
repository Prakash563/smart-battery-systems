import os
from django.conf import settings
from django.shortcuts import render, redirect
from .models import UserRegistrationModel
from django.contrib import messages

def UserRegisterActions(request):
    if request.method == 'POST':
        user = UserRegistrationModel(
            name=request.POST['name'],
            loginid=request.POST['loginid'],
            password=request.POST['password'],
            mobile=request.POST['mobile'],
            email=request.POST['email'],
            locality=request.POST['locality'],
            address=request.POST['address'],
            city=request.POST['city'],
            state=request.POST['state'],
            status='waiting'
        )
        user.save()
        messages.success(request,"Registration successful!")
    return render(request, 'UserRegistrations.html') 


def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('pswd')
        print("Login ID = ", loginid, ' Password = ', pswd)
        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            status = check.status
            print('Status is = ', status)
            if status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = loginid
                request.session['email'] = check.email
                data = {'loginid': loginid}
                print("User id At", check.id, status)
                return render(request, 'users/UserHomePage.html', {})
            else:
                messages.success(request, 'Your Account Not at activated')
                return render(request, 'UserLogin.html')
        except Exception as e:
            print('Exception is ', str(e))
            pass
        messages.success(request, 'Invalid Login id and password')
    return render(request, 'UserLogin.html', {})

def UserHome(request):
    return render(request, 'users/UserHomePage.html', {})


def index(request):
    return render(request,"index.html")

def ViewDataset(request):
    dataset = os.path.join(settings.MEDIA_ROOT, r'EV_Battery_SOHPrediction_Dataset_Extended.csv')
    import pandas as pd
    df = pd.read_csv(dataset, nrows=500)

    # Drop the first column (by index)
    df.drop(df.columns[0], axis=1, inplace=True)

    df = df.to_html(index=None)
    return render(request, 'users/viewData.html', {'data': df})
 

import random
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from .models import UserRegistrationModel

otp_storage = {}  # Temporary dictionary to store OTPs

def send_otp(email):
    otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
    otp_storage[email] = otp

    subject = "Password Reset OTP"
    message = f"Your OTP for password reset is: {otp}"
    from_email = "saikumardatapoint1@gmail.com"  # Change this to your email
    send_mail(subject, message, from_email, [email])

    return otp

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if UserRegistrationModel.objects.filter(email=email).exists():
            send_otp(email)
            request.session["reset_email"] = email  # Store email in session
            return redirect("verify_otp")
        else:
            messages.error(request, "Email not registered!")

    return render(request, "users/forgot_password.html")

def verify_otp(request):
    if request.method == "POST":
        otp_entered = request.POST.get("otp")
        email = request.session.get("reset_email")

        if otp_storage.get(email) and str(otp_storage[email]) == otp_entered:
            return redirect("reset_password")
        else:
            messages.error(request, "Invalid OTP!")

    return render(request, "users/verify_otp.html")

def reset_password(request):
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        email = request.session.get("reset_email")

        if UserRegistrationModel.objects.filter(email=email).exists():
            user = UserRegistrationModel.objects.get(email=email)
            user.password = new_password  # Updating password
            user.save()
            messages.success(request, "Password reset successful! Please log in.")
            return redirect("UserLoginCheck")

    return render(request, "users/reset_password.html")


## Machine Learning Code

import os
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import seaborn as sns
import plotly.graph_objects as go

# Load your dataset (make sure you place it correctly in the media folder or provide the full path)
df = pd.read_csv(r"media\EV_Battery_SOHPrediction_Dataset_Extended.csv")

def train_model(request):
    # Features and Target
    X = df.drop('SOH (%)', axis=1)
    y = df['SOH (%)']

    # Split into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize models
    models = {
        "XGBoost": XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        "LightGBM": LGBMRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42)
    }

    metrics = []
    graphs = []

    # Create directories if not exist
    os.makedirs("media/models", exist_ok=True)
    os.makedirs("media/graphs", exist_ok=True)

    # Correlation heatmap (only once)
    plt.figure(figsize=(10, 8))
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm')
    plt.title("Correlation Heatmap of Features")
    plt.tight_layout()
    heatmap_path = "media/graphs/correlation_heatmap.png"
    plt.savefig(heatmap_path)
    graphs.append(heatmap_path)
    plt.close()

    # Train, evaluate, and generate graphs
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        # Evaluation metrics
        mae = mean_absolute_error(y_test, preds)
        mse = mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        rmse = np.sqrt(mse)

        metrics.append({'model': name, 'mae': mae, 'mse': mse, 'r2': r2, 'rmse': rmse})

        # Save model
        joblib.dump(model, f"media/models/{name}_SOH_model.pkl")

        # Bar Graph - Evaluation Metrics
        plt.figure(figsize=(8, 5))
        plt.bar(['MAE', 'MSE', 'R2', 'RMSE'], [mae, mse, r2, rmse], color='skyblue')
        plt.title(f'{name} Evaluation Metrics')
        plt.xlabel('Metric')
        plt.ylabel('Value')
        graph_path = f"media/graphs/{name}_metrics.png"
        plt.savefig(graph_path)
        graphs.append(graph_path)
        plt.close()

        # Actual vs Predicted Plot
        plt.figure(figsize=(10, 6))
        plt.plot(y_test.values, label='Actual SOH', color='blue')
        plt.plot(preds, label='Predicted SOH', color='orange')
        plt.title(f"{name} - Actual vs Predicted SOH")
        plt.xlabel("Sample Index")
        plt.ylabel("SOH (%)")
        plt.legend()
        avp_path = f"media/graphs/{name}_actual_vs_predicted.png"
        plt.tight_layout()
        plt.savefig(avp_path)
        graphs.append(avp_path)
        plt.close()

        # Feature Importances (for tree-based models)
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            indices = np.argsort(importances)
            features = X.columns

            plt.figure(figsize=(10, 6))
            plt.barh(range(len(indices)), importances[indices], align='center')
            plt.yticks(range(len(indices)), [features[i] for i in indices])
            plt.xlabel("Feature Importance")
            plt.title(f"{name} - Feature Importance")
            feat_imp_path = f"media/graphs/{name}_feature_importance.png"
            plt.tight_layout()
            plt.savefig(feat_imp_path)
            graphs.append(feat_imp_path)
            plt.close()

    # Render page with metrics and all graphs
    return render(request, 'users/model_metrics.html', {'metrics': metrics, 'graphs': graphs})




def predict_soh_form(request):
    # Handle form for input
    if request.method == 'POST':
        # Get user input
        voltage = float(request.POST['voltage'])
        current = float(request.POST['current'])
        temperature = float(request.POST['temperature'])
        charge_cycles = int(request.POST['charge_cycles'])
        discharge_cycles = int(request.POST['discharge_cycles'])
        avg_charge_rate = float(request.POST['avg_charge_rate'])
        avg_discharge_rate = float(request.POST['avg_discharge_rate'])
        time_elapsed = float(request.POST['time_elapsed'])

        # Load the trained model (XGBoost example)
        model = joblib.load('media/models/XGBoost_SOH_model.pkl')

        # Predict SOH
        features = np.array([[voltage, current, temperature, charge_cycles, discharge_cycles,
                              avg_charge_rate, avg_discharge_rate, time_elapsed]])
        predicted_soh = model.predict(features)[0]

        # Threshold-based description
        description = get_soh_description(predicted_soh)
        
        # Time-to-replacement and health recommendations
        time_to_replacement = calculate_time_to_replacement(predicted_soh)
        recommendations = get_health_recommendations(predicted_soh)


        

        # Render result page
        return render(request, 'users/result.html', {
            'voltage': voltage, 'current': current, 'temperature': temperature,
            'charge_cycles': charge_cycles, 'discharge_cycles': discharge_cycles,
            'avg_charge_rate': avg_charge_rate, 'avg_discharge_rate': avg_discharge_rate,
            'time_elapsed': time_elapsed, 'predicted_soh': predicted_soh,
            'description': description, 'time_to_replacement': time_to_replacement,
            'recommendations': recommendations
        })
    
    return render(request, 'users/predict_soh_form.html')

def get_soh_description(soh):
    if soh > 80:
        return "Battery health is good."
    elif soh > 50:
        return "Battery health is fair. Consider monitoring."
    else:
        return "Battery health is poor. Time for replacement."

def calculate_time_to_replacement(soh):
    # Simple estimation logic based on SOH
    if soh > 80:
        return "More than 2 years"
    elif soh > 50:
        return "1 to 2 years"
    else:
        return "Less than 1 year"

def get_health_recommendations(soh):
    if soh > 80:
        return "Keep battery at optimal temperature and avoid overcharging."
    elif soh > 50:
        return "Regular monitoring is recommended. Avoid high charge cycles."
    else:
        return "Replace battery for optimal performance."


def project_overview(request):
    return render(request, 'users/project_overview.html')

