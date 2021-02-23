
import os.path
from enum import Enum

import base64
from io import BytesIO

import pandas as pd
from matplotlib.figure import Figure
from matplotlib import rcParams


import numpy as np


from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

import sklearn.cluster as cluster

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from sklearn import config_context

import time

def make_regression_plot(data_frame, x_axis, y_axis, user_point_x=None):
    df = data_frame[[x_axis, y_axis]].dropna()
    x_df = pd.DataFrame(df[x_axis])
    y_df = pd.DataFrame(df[y_axis])

    # Finds regression
    is_error = False
    try:
        model = LinearRegression()
        
        # Splits data with random state set to an integer and shuffle to false for reproducible output across multiple function calls
        x_df_train, x_df_test, y_df_train, y_df_test = train_test_split(x_df, y_df, random_state=10, shuffle=False)
        model.fit(x_df_train, y_df_train)
        
        y_df_test_pred = model.predict(x_df_test)
        
        the_mean_squared_error = mean_squared_error(y_df_test, y_df_test_pred)
        the_variance_score = r2_score(y_df_test, y_df_test_pred)
        
        y_df_pred = model.predict(x_df)

    # When there is less than 2 samples then can't do regression:
    except ValueError:
        is_error = True
       
    # Creates figure
    fig = Figure()
    ax = fig.subplots()
    ax.set_xlabel(x_axis)
    ax.set_ylabel(y_axis)

    # Plots scatter
    ax.scatter(x_df, y_df)

    # Plots regression if there is enough data to do so
    if not is_error:
        ax.plot(x_df, y_df_pred, label="regression", color="red")

    # Creates data for html image tag
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")

    # user_point_x prediction
    if user_point_x and not is_error:
        user_point_x = [[user_point_x]]
        user_point_y_pred = model.predict(user_point_x)[0][0]
        return (f"<img src='data:image/png;base64,{data}'/>" +
                f"<h3>The recommended value is: ${user_point_y_pred}</h3>" +
                f"<h3>The mean squared error is: {the_mean_squared_error}</h3>" +
                f"<h3>The variance score is: {the_variance_score}</h3>")
    else:
        return (f"<img src='data:image/png;base64,{data}'/>" + 
                f"<h3>There is not enough data with the given characteristics to create the regression</h3>")
            
def estimate_overall_accuracy(data_frame, x_axis, y_axis, column_name, values):
    model = LinearRegression()
    the_mean_squared_errors = []
    the_variance_scores = []

    for value in values:
        df = data_frame[data_frame[column_name] == value]
        df = data_frame[[x_axis, y_axis]].dropna()
        x_df = pd.DataFrame(df[x_axis])
        y_df = pd.DataFrame(df[y_axis])
        # Finds regression
        try:
            # Splits data with random state set to an integer and shuffle to false for reproducible output across multiple function calls
            x_df_train, x_df_test, y_df_train, y_df_test = train_test_split(x_df, y_df, random_state=10, shuffle=False)
            model.fit(x_df_train, y_df_train)
        
            y_df_test_pred = model.predict(x_df_test)
        
            the_mean_squared_errors.append(mean_squared_error(y_df_test, y_df_test_pred))
            the_variance_scores.append(r2_score(y_df_test, y_df_test_pred))

        # When there is less than 2 samples then can't do regression:
        except ValueError as e:
            print(e)
            pass
    if len(the_mean_squared_errors) != 0 and len(the_variance_scores) != 0:
        average_mean_squared_error = sum(the_mean_squared_errors) / len(the_mean_squared_errors)
        average_variance_score = sum(the_variance_scores) / len(the_variance_scores)
    else:
        average_mean_squared_error = "NA"
        average_variance_score = "NA"
    print(f"average mean squared error: {average_mean_squared_error} \n" +
          f"average variance score: {average_variance_score}")

def make_dashboard_plots(data_frame, plot_options):
    start_time = time.perf_counter()

    # Creates figure
    fig_width = 8
    fig_height = (8*len(plot_options))
    fig = Figure(figsize=[fig_width, fig_height])
    nrows = len(plot_options)
    ncols = 1
    axes = fig.subplots(nrows=nrows, ncols=ncols, squeeze=False)
    
    # Because there is only 1 column there is only one column_index
    column_index = 0
    for row_index in range(nrows):
        plot_option = plot_options[row_index]
        plot_type = plot_option.plot_type
        x_axis = plot_option.x_axis
        y_axis = plot_option.y_axis
        ax = axes[row_index][column_index]

        if plot_type == PlotType.BAR:
            df_bar = data_frame.groupby(x_axis).mean()
            df_bar.plot.bar(y=y_axis, ax=ax, ylabel=f"mean {y_axis}", legend=False)
        elif plot_type == PlotType.BOXPLOT:
            df_boxplot = data_frame[[x_axis, y_axis]]
            df_boxplot.boxplot(by=x_axis, ax=ax, showfliers=False)
            ax.set_title("")
            ax.set_xlabel(x_axis)
            ax.set_ylabel(y_axis)
        elif plot_type == PlotType.LINE:
            data_frame.plot(x_axis, y_axis, ax=ax)
        elif plot_type == PlotType.SCATTER:
            # Drops NA values
            df_scatter = data_frame[[x_axis, y_axis]].dropna()
            
            x_df = pd.DataFrame(df_scatter[x_axis])
            y_df = pd.DataFrame(df_scatter[y_axis])
            try:
                # Calculates KMeans clusters 
                cluster_y_pred = cluster.KMeans(n_clusters=4).fit_predict(x_df, y_df)
               
                # Plots data points colored according to assigned cluster
                ax.scatter(x_df, y_df, c=cluster_y_pred)
                ax.set_xlabel(x_axis)
                ax.set_ylabel(y_axis)
                
            # When there is less than 2 samples then can't do cluster:
            except ValueError as error:
                # Plots data points
                raise error
                df_scatter.plot.scatter(x_axis, y_axis, ax=ax)

        elif plot_type == PlotType.PIE:
            pie_df = data_frame.groupby(y_axis).size()
            pie_df.plot.pie(y=y_axis, ax=ax, title=y_axis, legend=True, autopct="%1.1f%%", labels=None, explode=[0.1 for i in range(len(pie_df.index))] )
                 
    # Creates data for html image tag
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    
    end_time = time.perf_counter()
    print(f"took {end_time - start_time:0.4f} seconds")
    
    return f"<img src='data:image/png;base64,{data}'/>"

class PlotType(Enum):
    BAR = "bar"
    BOXPLOT = "boxplot"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
   
def make_PCA_plot(data_frame, columns):
    df = data_frame[columns].dropna()
    print(df.head())
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)
    print(f"scaled: {scaled_data[:5]}")

    pca= PCA()
    X_pca = pca.fit_transform(scaled_data)
    print(f"pca variance ratio{(pca.explained_variance_ratio_ * 100)}" +
          f"\n pca singular_values_{pca.singular_values_}" +
          f"\n pca n_features_{pca.n_features_}")

    # Creates figure
    fig = Figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(X_pca[:,0], X_pca[:,1], X_pca[:,2])
    

    # Creates data for html image tag
    buf = BytesIO()
    fig.savefig(buf, format="png")
    data = base64.b64encode(buf.getbuffer()).decode("ascii")

    return f"<img src='data:image/png;base64,{data}'/>"
