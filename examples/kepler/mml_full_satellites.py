# Copyright (c) 2013-2016 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np

import bayeslite
import bdbcontrib

from bdbcontrib.bql_utils import query
from bdbcontrib.metamodels.composer import Composer
from bdbcontrib.predictors import keplers_law
from bdbcontrib.predictors import multiple_regression
from bdbcontrib.predictors import random_forest

from bdbcontrib.predictors.keplers_law import satellite_period_minutes

# Global constants.
GM = 398600.4418
EARTH_RADIUS = 6378
T = 1436

# Helper functions.
def compute_period(apogee_km, perigee_km):
    """Computes the period of the satellite in seconds given the apogee_km
    and perigee_km of the satellite.
    """
    a = 0.5*(abs(apogee_km) + abs(perigee_km)) + EARTH_RADIUS
    T = 2 * np.pi * np.sqrt(a**3/GM) / 60.
    return T

def compute_a(T):
    a = ((60*T/(2*np.pi))**2 * GM)**(1./3)
    return a

def compute_T(a):
    T = 2 * np.pi * np.sqrt(a**3/GM) / 60.
    return T

def create_bdb():
    # Load the bdb.
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    bdb = bayeslite.bayesdb_open('bdb/%s.bdb' % timestamp)

    # Load satellites data.
    bayeslite.bayesdb_read_csv_file(bdb, 'satellites',
        'resources/satellites_all.csv', header=True, create=True)
    bdbcontrib.nullify(bdb, 'satellites', 'NaN')
    return bdb

def retrieve_bdb(filename):
    # Register MML models.
    bdb = bayeslite.bayesdb_open(filename)
    composer = Composer()
    composer.register_foreign_predictor(keplers_law.KeplersLaw)
    composer.register_foreign_predictor(random_forest.RandomForest)
    composer.register_foreign_predictor(multiple_regression.MultipleRegression)
    bayeslite.bayesdb_register_metamodel(bdb, composer)
    return bdb

def create_initialize_analyze(bdb):
    # Create default gpm.
    bdb.execute('''
        CREATE GENERATOR t11 FOR satellites USING crosscat(
            GUESS(*));''')
    bdb.execute('INITIALIZE 64 MODELS FOR t11;')
    bdb.execute('ANALYZE t11 FOR 200 ITERATION WAIT;')
    # Create the GPMs.
    bdb.execute('''
        CREATE GENERATOR t12 FOR satellites USING composer(
            default (
                Country_of_Operator CATEGORICAL, Operator_Owner CATEGORICAL,
                Users CATEGORICAL, Purpose CATEGORICAL,
                Type_of_Orbit CATEGORICAL, Perigee_km NUMERICAL,
                Apogee_km NUMERICAL, Eccentricity NUMERICAL,
                Launch_Mass_kg NUMERICAL, Dry_Mass_kg NUMERICAL,
                Power_watts NUMERICAL, Date_of_Launch NUMERICAL,
                Contractor CATEGORICAL,
                Country_of_Contractor CATEGORICAL, Launch_Site CATEGORICAL,
                Launch_Vehicle CATEGORICAL,
                Source_Used_for_Orbital_Data CATEGORICAL,
                longitude_radians_of_geo NUMERICAL,
                Inclination_radians NUMERICAL,
            ),
            random_forest (
                Class_of_orbit CATEGORICAL
                    GIVEN Apogee_km, Perigee_km,
                        Eccentricity, Period_minutes, Launch_Mass_kg,
                        Power_watts, Anticipated_Lifetime, Type_of_Orbit
            ),
            keplers_law (
                Period_minutes NUMERICAL
                    GIVEN Perigee_km, Apogee_km
            ),
            multiple_regression (
                Anticipated_Lifetime NUMERICAL
                    GIVEN Dry_Mass_kg, Power_watts, Launch_Mass_kg, Contractor
            ),
            DEPENDENT(Apogee_km, Perigee_km, Eccentricity),
        );''')

    print 'Init'
    bdb.execute('INITIALIZE 64 MODELS FOR t12;')
    print 'Analyz'
    bdb.execute('ANALYZE t12 FOR 150 ITERATION WAIT;')


def plot_T_given_CO(bdb):
    create = False
    if create:
        leo = bdb.execute('''SELECT Period_minutes FROM satellites WHERE
            Class_of_orbit = "LEO"''').fetchall()
        geo = bdb.execute('''SELECT Period_minutes FROM satellites WHERE
            Class_of_orbit = "GEO"''').fetchall()
        meo = bdb.execute('''SELECT Period_minutes FROM satellites WHERE
            Class_of_orbit = "MEO"''').fetchall()
        elliptical = bdb.execute('''SELECT Period_minutes FROM satellites
            WHERE Class_of_orbit = Elliptical''').fetchall()
        samples_leo = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "LEO" LIMIT 100;''').fetchall()
        samples_geo = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "GEO" LIMIT 100;''').fetchall()
        samples_meo = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "MEO" LIMIT 100;''').fetchall()
        samples_elliptical = bdb.execute('''SIMULATE Period_minutes FROM t12 GIVEN
            Class_of_orbit = "Elliptical" LIMIT 100;''').fetchall()
    else:
        leo = np.loadtxt('resources/TgCO/leo')
        geo = np.loadtxt('resources/TgCO/geo')
        meo = np.loadtxt('resources/TgCO/meo')
        elliptical = np.loadtxt('resources/TgCO/elliptical')
        samples_leo = list(np.loadtxt('resources/TgCO/samples_leo'))
        samples_geo = list(np.loadtxt('resources/TgCO/samples_geo'))
        samples_meo = list(np.loadtxt('resources/TgCO/samples_meo'))
        samples_elliptical = list(np.loadtxt('resources/TgCO/samples_elliptical'))

    fig, ax = plt.subplots(2,1)

    ax[0].hlines(leo, xmin=0, xmax=1, label='LEO', color='blue')
    ax[0].hlines(geo, xmin=1, xmax=2, label='MEO', color='red')
    ax[0].hlines(meo, xmin=2, xmax=3, label='GEO', color='green')
    ax[0].hlines(elliptical, xmin=3, xmax=4, label='Elliptical', color='black')
    ax[0].set_title('SELECT Period_minutes, Class_of_orbit FROM'
        ' satellites ORDER BY Class_of_orbit''', fontweight='bold',size=16)

    ax[1].hlines(samples_leo[:10]+samples_leo[-10:], xmin=0, xmax=1,
        label='LEO', color='blue')
    ax[1].hlines(samples_meo[:10]+samples_meo[-10:],
        xmin=1, xmax=2, label='MEO', color='red')
    ax[1].hlines(samples_geo[60:70] + samples_geo[80:90],
        xmin=2, xmax=3, label='GEO', color='green')
    ax[1].hlines(samples_elliptical[:10]+samples_elliptical[-10:],
        xmin=3, xmax=4, label='Elliptical', color='black')
    ax[1].set_title('''
        SIMULATE Period_minutes FROM satellites GIVEN Class_of_orbit''',
        fontweight='bold', size=16)

    for a in ax:
        a.set_xlim([0,4])
        a.set_xlim([0,4])
        a.set_ylim([0,4000])
        a.set_ylim([0,4000])
        a.set_xticks([0.5, 1.5, 2.5, 3.5])
        a.set_xticklabels(['LEO','MEO','GEO','Elliptical'])
        a.set_ylabel('Period (minutes)', fontweight='bold', size=16)
        a.grid()
        a.grid()


def plot_period_perigee_given_purpose(bdb):
    # Create the simulations.
    # bdb.execute("""
    #     CREATE TABLE period_perigee_given_purpose_t11 AS
    #         SIMULATE perigee_km, period_minutes FROM t11
    #         GIVEN purpose = 'Communications' LIMIT 1000;""")
    # bdb.execute("""
    #     CREATE TABLE period_perigee_given_purpose_t12 AS
    #         SIMULATE perigee_km, period_minutes FROM t12
    #         GIVEN purpose = 'Communications' LIMIT 100;""")

    # Extract data to arrays.
    t11 = np.asarray(bdb.execute(
        'SELECT * FROM period_perigee_given_purpose_t11 LIMIT 75;').fetchall())
    t12 = np.asarray(bdb.execute(
        'SELECT * FROM period_perigee_given_purpose_t12 LIMIT 75;').fetchall())

    # Prepare figure.
    fig, ax = plt.subplots(nrows=1, ncols=2)
    fig.suptitle('SIMULATE period_minutes, perigee_km '
        'GIVEN purpose = \'Communications\'', fontweight='bold', fontsize=18)

    # Scatter crosscat.
    ax[0].scatter(
        t11[:,0], t11[:,1], color='r', label='Crosscat', s=8)
    ax[0].set_xlim(-1000, 48000)
    ax[0].set_ylim(-100, 1800)

    # Scatter Kepler + Crosscat.
    ax[1].scatter(
        t12[:,0], t12[:,1], color='g', label='Crosscat + Kepler', s=8)
    ax[1].set_xlim(*ax[1].get_xlim())
    ax[1].set_ylim(*ax[1].get_ylim())

    # Grids and legends.
    for a in ax:
        a.grid()
        a.legend(framealpha=0, loc='upper left')
        a.set_xlabel('Perigee [km]', fontweight='bold', fontsize=12)
        a.set_ylabel('Period [mins]', fontweight='bold', fontsize=12)


def plot_period_perigee_cluster(bdb):
    # Select empirical data from joint.
    t11 = query(bdb,
        """SELECT perigee_km, period_minutes, apogee_km
            FROM satellites""").as_matrix()

    COLORS = ['red','green','blue','magenta','purple','orange','orange',
        'orange','orange','orange']

    # import ipdb; ipdb.set_trace()
    name0, perigee0, period0, index0, = 'Orion6', 35771, 23.94, 10
    name1, perigee1, period1, index1, = 'Geotail', 7079.0, 2872.15, 331
    name2, perigee2, period2, index2, = 'Meridian4', 961, 645, 646

    # t12[ (t12['Perigee_km']<35600) & (t12['Perigee_km']>35580)] 53
    name3, perigee3, period3, index3 = 'Amos5', 35595, 1436, 53

    name4, perigee4, period4, index4 = 'NavStar', 20188, 718, 685

    plot_names = [name0, name1, name2, name3, name4]
    plot_perigees = [perigee0, perigee1, perigee2, perigee3, perigee4]
    plot_periods = [period0, period1, period2, period3, period4]
    indexes = [index0, index1, index2, index3, index4]


    # Find four satellites to plot.
    t12 = query(bdb,
        """SELECT perigee_km, period_minutes, apogee_km, name
            FROM satellites""")
    t13 = np.asarray(t12.iloc[:,:2])

    def plot_satellite_scatter(ax, clusters, colors):
        ax.set_title('Clusters Identified by Kepler CPGM',
            fontweight='bold', fontsize=18)
        for ix in reversed([2,3,1,0,4,5,6,7,8]):
            points = t13[clusters==ix]
            print ix, len(points), colors[ix]
            ax.scatter(points[:,0], points[:,1], color=colors[ix])

        #  -- Parameterize by eccentricity.
        ecc = [.0, .9]
        perigees = np.linspace(np.min(t11[~np.isnan(t11[:,0])][:,0]), 48000, 100)
        compute_apogees = lambda ecc:\
            (perigees + EARTH_RADIUS) * (1+ecc)/(1-ecc) - EARTH_RADIUS
        apogees_ecc = map(compute_apogees, ecc)
        periods_ecc = [compute_period(ap_ecc, perigees) for ap_ecc in apogees_ecc]

        ax.fill_between(
            perigees, periods_ecc[0], periods_ecc[1], color='gray', alpha=0.2,
            label='Theoretically\nFeasible Orbits')

        # Put the names
        for nm, prg, prd in zip(plot_names, plot_perigees, plot_periods):
            ax.text(
                prg-3000, prd+200, nm, fontdict={'weight':'bold', 'size':12})

        # Grids and legends.
        ax.set_xlim([-2500, 48000])
        ax.set_ylim([-500, 5000])
        ax.grid()
        ax.legend(framealpha=0, loc='upper right')
        ax.set_xlabel('Perigee [km]', fontweight='bold', fontsize=18)
        ax.set_ylabel('Period [mins]', fontweight='bold', fontsize=18)

    def plot_error_distribution(ax, errors, clusters, colors):
        t12 = query(bdb,
            """SELECT perigee_km, period_minutes, apogee_km, name
                FROM satellites""")
        t13 = np.asarray(t12.iloc[:,:2])
        errors = np.log10(errors)
        ax.set_title(
            'Empirical Distribution of Orbital Deviations', fontweight='bold',
            fontsize=18)
        for ix in set(clusters):
            samples = errors[clusters==ix]
            ax.hist(samples, bins=50, alpha=1, color=colors[ix], normed=0)
        # Annotate the outlier satellites.
        props = dict(facecolor='black', width=1)
        # import ipdb; ipdb.set_trace()
        ax.annotate(plot_names[0],
            xy=(errors[indexes[0]], 1),
            xytext=(errors[indexes[0]]+1, 3),
            arrowprops=props,
            weight='bold',
            size=14)
        ax.annotate(plot_names[1],
            xy=(errors[indexes[1]], 1),
            xytext=(0, 40),
            arrowprops=props,
            weight='bold',
            size=14)
        ax.annotate(plot_names[2],
            xy=(errors[indexes[2]], 1),
            xytext=(errors[indexes[2]]+1, 5),
            arrowprops=props,
            weight='bold',
            size=14)
        ax.annotate(plot_names[3],
            xy=(errors[indexes[3]], 1),
            xytext=(1, 5),
            arrowprops=props,
            weight='bold',
            size=14)
        # ax.annotate(plot_names[4],
        #     xy=(samples[indexes[4]], 2),
        #     xytext=(0, 20),
        #     arrowprops=props,
        #     weight='bold',
        #     size=14)
        ax.set_xlabel(
            'Magntiude of Deviation from Kepler\'s Law [mins]',
            fontweight='bold', fontsize=18)
        ax.set_ylabel(
            'Number of Satellites',
            fontweight='bold', fontsize=18)
        ax.set_yscale('log', basey=2)
        labels = ['1e%1.f'%x for x in ax.get_xticks()]
        ax.set_xticklabels(labels)
        ax.grid()

    inferred_clusters = query(bdb,
        'SELECT * FROM inferred_orbital_cluster').values.ravel().astype(int)
    inferred_noise = query(bdb,
        'SELECT * FROM inferred_orbital_noise;').values
    inferred_errors = (inferred_noise**2).ravel()

    fig, ax = plt.subplots()
    plot_satellite_scatter(ax, inferred_clusters, COLORS)

    fig, ax = plt.subplots()
    plot_error_distribution(
        ax, inferred_errors, inferred_clusters, COLORS)

bdb = retrieve_bdb('/scratch/fs/gpmcc/examples/satellites/kep/kep.bdb')
plot_period_perigee_cluster(bdb)