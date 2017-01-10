# -*- coding: utf-8 -*-

# Copyright (c) 2016 by University of Kassel and Fraunhofer Institute for Wind Energy and Energy
# System Technology (IWES), Kassel. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

import scipy.io
import numpy as np

from pandapower.converter import from_ppc
try:
    import pplog as logging
except:
    import logging

logger = logging.getLogger(__name__)


def from_mpc(mpc_file, f_hz=50, detect_trafo='vn_kv', casename_mpc_file='mpc'):
    """
    This function converts a matpower case file (.mat) version 2 to a pandapower net.
    Note: python is 0-based while Matlab is 1-based.

    INPUT:

        **mpc_file** - path to a matpower case file (.mat).

    OPTIONAL:

        **f_hz** (int, 50) - The frequency of the network.

        **detect_trafo** (str, 'vn_kv') - In case of 'vn_kv' trafos are detected by different bus voltages.
            In case of 'ratio' trafos are detected by tap ratios != 0.

        **casename_mpc_file** (str, 'mpc') - If mpc_file does not contain the arrays "gen", "branch" and "bus" it will use the
            sub-struct casename_mpc_file

    OUTPUT:

        **net** - The pandapower network

    EXAMPLE:

        import pandapower.converter as pc

        pp_net = cv.from_ppc('case9.mat', f_hz=60)

    """
    ppc = _mpc2ppc(mpc_file, casename_mpc_file)
    net = from_ppc(ppc, f_hz, detect_trafo)

    return net


def _mpc2ppc(mpc_file, casename_mpc_file):
    # load mpc from file
    mpc = scipy.io.loadmat(mpc_file, squeeze_me=True, struct_as_record=False)

    # init empty ppc
    ppc = dict()

    _copy_data_from_mpc_to_ppc(ppc, mpc, casename_mpc_file)
    _adjust_ppc_indices(ppc)
    _change_ppc_TAP_value(ppc)

    return ppc


def _adjust_ppc_indices(ppc):
    # adjust indices of ppc, since ppc must start at 0 rather than 1 (matlab)
    ppc["bus"][:, 0] -= 1
    ppc["branch"][:, 0] -= 1
    ppc["branch"][:, 1] -= 1
    ppc["gen"][:, 0] -= 1


def _copy_data_from_mpc_to_ppc(ppc, mpc, casename_mpc_file):
    if casename_mpc_file in mpc:
        # if struct contains a field named mpc
        ppc['version'] = mpc[casename_mpc_file].version
        ppc["baseMVA"] = mpc[casename_mpc_file].baseMVA
        ppc["bus"] = mpc[casename_mpc_file].bus
        ppc["gen"] = mpc[casename_mpc_file].gen
        ppc["branch"] = mpc[casename_mpc_file].branch

        try:
            ppc['gencost'] = mpc[casename_mpc_file].gencost
        except:
            logger.info('gencost is not in mpc')

    elif 'bus' in mpc \
            and 'branch' in mpc \
            and 'gen' in mpc \
            and 'baseMVA' in mpc \
            and 'version' in mpc:

        # if struct contains bus, branch, gen, etc. directly
        ppc['version'] = mpc['version']
        ppc["baseMVA"] = mpc['baseMVA']
        ppc["bus"] = mpc['bus']
        ppc["gen"] = mpc['gen']
        ppc["branch"] = mpc['branch']

        if 'gencost' in mpc:
            ppc['gencost'] = mpc['gencost']
        else:
            logger.info('gencost is not in mpc')

    else:
        logger.error('Matfile does not contain a valid mpc structure')


def _change_ppc_TAP_value(ppc):
    # adjust for the matpower converter -> taps should be 0 when there is no transformer, but are 1
    ppc["branch"][np.where(ppc["branch"][:, 8] == 0), 8] = 1