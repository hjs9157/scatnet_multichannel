'''module for performing invariant scattering transformation on multichannel time series'''
import os
import numpy as np

'''
FIXME: consider name change for filter_options, filter_type
'''

def T_to_J(T, filt_opt):
    '''
    calculates maximal wavelet scale J
    
    inputs:
    -------
    - T: int type, length of signal in units of samples
    - filt_opt: dict type object with parameters specifying a filter

    outputs:
    --------
    - J: list type with elements int type. maximal wavelet scale

    FIXME: consider name change of Q, B, J, filt_opt
    '''
    filt_opt = filt_opt.copy() # prevents filt_opt change upon function call
    filt_opt = fill_struct(filt_opt, Q=1)
    filt_opt = fill_struct(filt_opt, B=filt_opt['Q'])
    Q = filt_opt['Q']
    B = filt_opt['B']
    if isinstance(Q, list):
        bw_mult = list(1 + (np.array(Q)==1).astype('int'))
    else:
        bw_mult = 1 + int(np.array(Q)==1)
    filt_opt = fill_struct(filt_opt, phi_bw_multiplier=bw_mult)
    bw_mult = filt_opt['phi_bw_multiplier']
    if isinstance(Q, list) and isinstance(B, list):
        J = list(1 + np.round(np.log2(T / (4 * np.array(B) \
        / np.array(bw_mult))) * np.array(Q)).astype(int)) 
        # NOTE: indices should be type int
    elif Q > 0 and B > 0:
        J = 1 + int(np.round(np.log2(T / (4 * B / bw_mult)) * Q))
    else:
        raise ValueError("Invalid type of Q or B: must be list or numeric")
    
    return J

def default_filter_opt(filter_type, avg_len):
    '''
    returns dict type object containing default parameters for filters
    inputs:
    -------
    - filter_type: "audio", "dyadic". NOTE: potentially "image" to be added later
    - avg_len: int type number representing width of scaling function to apply in units of samples

    outputs:
    --------
    - s: dict type object containing default parameters for filters

    FIXME: change variable name s, consider allowing "image" as filter_type input
    '''
    s = {}
    if filter_type == 'audio':
        s['Q'] = [8, 1]
        s['J'] = T_to_J(avg_len, s)
    elif filter_type == 'dyadic':
        s['Q'] = 1
        s['J'] = T_to_J(avg_len, s)
    else:
        raise ValueError("Invalid filter_type: should be either audio or dyadic")
    return s

def fill_struct(s, **kwargs):
    '''
    for a given dictionary and a number of key-value pairs, fills in the key-values of the
    dictionary if the key does not exist or if the value of the key is empty

    inputs:
    -------
    - s: dict type that may or may not contain the keys given by user

    outputs:
    --------
    - s: type dict object that is updated with the given key-value pairs. For keys that
    originally did not exist, the key-value pair is updated. For keys that originally existed
    are updated only if the values were None
    
    FIXME: consider name change of s. Consider replacing function with more readable function''' 
    for key, value in kwargs.items():
        if key in s:
            if s[key] is None:
                s[key] = value
        else:
            s[key] = value
    return s

def morlet_freq_1d(filt_opt):
    '''
    inputs:
    ------- 
    - filt_opt: type dict with the following keys:
    xi_psi, sigma_psi, sigma_phi, J, Q, P: all numeric
    phi_dirac: type bool
    As all values in filt_opt dict are scalars, filt_opt argument does not change upon function call

    outputs:
    -------- 
    - xi_psi: list sized (J+P, ). logarithmically spaced J elements, linearly spaced P elements
    - bw_psi: list sized (J+P+1, ). logarithmically spaced J elements, linearly spaced P+1 elements
    both type nparray during calculations, convertable to list at final output
    - bw_phi: float
    
    increasing index corresponds to filters with decreasing center frequency
    filters with high freq are logarithmically spaced, low freq interval is covered linearly
    NOTE: xi_psi can in theory have negative center frequencies
    
    FIXME: consider defining local variables for the key-value pairs in filt_opt during calculations
    FIXME: consider not converting outputs to list type
    REVIEW: manually compare results with MATLAB version
    '''
    sigma0 = 2 / np.sqrt(3)
    
    # calculate logarithmically spaced band-pass filters.
    xi_psi = filt_opt['xi_psi'] * 2**(np.arange(0,-filt_opt['J'],-1) / filt_opt['Q'])
    sigma_psi = filt_opt['sigma_psi'] * 2**(np.arange(filt_opt['J']) / filt_opt['Q'])
    # calculate linearly spaced band-pass filters so that they evenly
    # cover the remaining part of the spectrum
    step = np.pi * 2**(-filt_opt['J'] / filt_opt['Q']) * (1 - 1/4 * sigma0 / filt_opt['sigma_phi'] \
        * 2**( 1 / filt_opt['Q'] ) ) / filt_opt['P']
    # xi_psi = np.array(xi_psi)
    # xi_psi[filt_opt['J']:filt_opt['J']+filt_opt['P']] = filt_opt['xi_psi'] * 2**((-filt_opt['J']+1) / filt_opt['Q']) - step * np.arange(1, filt_opt['P'] + 1)
    xi_psi_lin = filt_opt['xi_psi'] * 2**((-filt_opt['J']+1) / filt_opt['Q']) \
    - step * np.arange(1, filt_opt['P'] + 1)
    xi_psi = np.concatenate([xi_psi, xi_psi_lin], axis=0) 
    # sigma_psi = np.array(sigma_psi)
    # sigma_psi[filt_opt['J']:filt_opt['J']+1+filt_opt['P']] = filt_opt['sigma_psi'] * 2**((filt_opt['J'] - 1) / filt_opt['Q'])
    sigma_psi_lin = np.full((1+filt_opt['P'],), fill_value=filt_opt['sigma_psi'] \
        * 2**((filt_opt['J'] - 1) / filt_opt['Q']))
    sigma_psi = np.concatenate([sigma_psi, sigma_psi_lin], axis=0)
    # calculate band-pass filter
    sigma_phi = filt_opt['sigma_phi'] * 2**((filt_opt['J']-1) / filt_opt['Q'])
    # convert (spatial) sigmas to (frequential) bandwidths
    bw_psi = np.pi / 2 * sigma0 / sigma_psi
    if not filt_opt['phi_dirac']:
        bw_phi = np.pi / 2 * sigma0 / sigma_phi
    else:
        bw_phi = 2 * np.pi
    return list(xi_psi), list(bw_psi), bw_phi

def optimize_filter(filter_f, lowpass, options):
    options = fill_struct(options, truncate_threshold=1e-3);
    options = fill_struct(options, filter_format=fourier_multires);

    if options.filter_format == 'fourier':
        filt = filter_f
    elif options.filter_format == 'fourier_multires':
        filt = periodize_filter(filter_f)
    elif options.filter_format == 'fourier_truncated':
        filt = truncate_filter(filter_f, options.truncate_threshold, lowpass)
    else:
        raise ValueError('Unknown filter format {}'.format(options.filter_format))
    return filt

def filter_freq(filter_options):
    if (filter_options['filter_type'] == 'spline_1d') or (filter_options['filter_type'] == 'selesnick_1d'):
        psi_xi, psi_bw, phi_bw = dyadic_freq_1d(filter_options)
    elif (filter_options['filter_type'] == 'morlet_1d') or (filter_options['filter_type'] == 'gabor_1d'):
        psi_xi, psi_bw, phi_bw = morlet_freq_1d(filter_options)
    else:
        raise ValueError('Unknown filter type {}'.format(filter_options['filter_type']))
    return psi_xi, psi_bw, phi_bw

def map_meta(from_meta, from_ind, to_meta, to_ind, exclude=None):
    '''
    for all key-value pairs in from_meta, the columns are copied into the to_meta's key-value pairs
    including key value pairs not existing in to_meta while excluding the list of key value pairs in
    the argument "exclude". If the number of indices differ, the columns of from_ind are tiled
    to match the number of columns of to_ind
    
    inputs:
    -------
    - from_meta: dict type object
    - from_ind: list type containing indices
    - to_meta: dict type object
    - to_ind: list type containing indices
    - exclude: list type object containing keys that should not be considered when copying columns 
    For a single index, a scalar is allowed which will be cast to a length 1 list in the function

    NOTE: assumed that from_meta's values are valid 2d lists or rank 2 np arrays
    NOTE: MATLAB version can run with less input arguments
    FIXME: if to_ind has 4 indices and from_ind has 2 indices, the columns are copied by a factor
    of 2 to match the 4 columns. confirm this is the desired functionality.

    FIXME: for shared keys, if to_ind goes out of bound, should to_meta's shared key be
    extended to incorporate that? or should it raise an error? Current version does not extend
    '''
    if isinstance(from_ind, int):
        from_ind = [from_ind]

    if isinstance(to_ind, int):
        to_ind = [to_ind]

    if not to_ind or not from_ind:
        # since to_ind and from_ind are lists for int inputs, 
        # no need to worry about an input of 0 for to_ind treated as an empty list
        # if to_ind or from_ind are empty, do nothing to to_meta
        return to_meta

    if exclude is None:
        exclude = []

    # NOTE: from_meta's fields should be arrays or 2d lists with fixed sizes
    # different 0th indices correspond to different columns in the MATLAB version
    for key, value in from_meta.items(): 
    # NOTE: loops through from_meta's keys. Thus, for to_meta's pure keys (keys that only exist
    # in to_meta but not from_meta), the values are identical
        if key in exclude: 
            continue
        
        if key in to_meta.keys():
            to_value = np.zeros((max(max(to_ind) + 1, len(to_meta[key])), value.shape[1]))
            to_value[:len(to_meta[key]), :] = np.array(to_meta[key])
            # the version below raises error later if to_ind goes out of to_meta[key]'s index
            # to_value = np.array(to_meta[key]) 
        else:
            to_value = np.zeros((max(to_ind)+1, value.shape[1]))
        to_value[to_ind, :] = np.tile(value[from_ind, :], [int(len(to_ind) / len(from_ind)), 1])
        to_meta[key] = to_value

    return to_meta

def conv_sub_1d(xf, filt, ds):
    xf = np.array(xf)
    sig_length = len(xf)
    if len(xf.shape) == 1:
        xf = xf[np.newaxis, :] # FIXME: for 1 signal, a singleton dim added. consider refactoring
    n_data = xf.shape[0]

    # FIXME:NOTE: filt assumed to be either dict, list, or np.array. xf assumed to be either np.array or list
    # FIXME: filt assumed to be rank 1
    if isinstance(filt, dict):
        # optimized filt, output of OPTIMIZE_FILTER
        if filt['type'] == 'fourier_multires':
            # NOTE: filt['coefft'] is assumed to be a LIST of filters where each filter is rank 1
            # periodized multiresolution filt, output of PERIODIZE_FILTER
            # make filt_coefft into rank 2 array sized (1, filt_len)
            filt_coefft = filt['coefft'][int(np.round(np.log2(filt['N'] / sig_length)))]
            filt_coefft = np.array(filt_coefft)[np.newaxis, :] 
            yf = xf * np.tile(filt_coefft, (n_data, 1)) 
            print("\nfilter is dict and its type is fourier_multires")
            print("filt_j:{}".format(filt_j))
            print("yf:{}".format(yf))
        # for now, only consider the case for 'fourier_multires'
        elif filt['type'] == 'fourier_truncated':
            # in this case, filt['coefft'] is assumed to be an array 
            # truncated filt, output of TRUNCATE_FILTER
            start = filt['start']
            coefft = filt['coefft']
            nCoeffts = len(coefft)
            coefft = np.array(coefft)
            if nCoeffts > sig_length:
                # filt is larger than signal, lowpass filt & periodize the former
                # create lowpass filt
                start0 = start % filt['N']
                nCoeffts = nCoeffts
                if (start0 + nCoeffts) <= filt['N']:
                    rng = np.arange(start0, nCoeffts - 1)
                else:
                    rng = np.concatenate([np.arange(start0, filt['N']), np.arange(nCoeffts + start0 - filt['N'])], axis=0)

                lowpass = np.zeros(nCoeffts)
                lowpass[rng < sig_length / 2] = 1
                lowpass[rng == sig_length / 2] = 1/2
                lowpass[rng == filt['N'] - sig_length / 2] = 1/2
                lowpass[rng > filt['N'] - sig_length / 2] = 1
                # filter and periodize
                coefft = np.reshape(coefft * lowpass, [sig_length, int(nCoeffts / sig_length)]).sum(axis=1)
                coefft = coefft[np.newaxis, :]

            j = int(np.round(np.log2(nCoeffts / sig_length)))
            start = start % sig_length
            if start + nCoeffts <= sig_length:
                # filter support contained in one period, no wrap-around
                yf = xf[:, start:nCoeffts+start-1] * np.tile(coefft, (n_data, 1))
            else:
                # filter support wraps around, extract both parts
                yf = np.concatenate([xf[:, start:], xf[:, :nCoeffts + start - size(xf,1)]], axis=1) * np.tile(coefft, (n_data, 1))

            print("\nfilter is dict and its type is fourier_truncated")
            print("filt_j:{}".format(filt_j))
            print("yf:{}".format(yf))
    else:
        # type is either list or nparray
        filt = np.array(filt)
        # simple Fourier transform. filt_j below has length equal to sig_length.
        # filt_j is a fraction taken from filt to match length with sig_length.
        # if sig_length is [10,11,12,13,14,15] and filt being range(100), 
        # filt_j would be [0, 1, 2, (3 + 98)/2, 99, 100].
        # REVIEW: figure out why the shifting is done before multiplying. 
        # Perhaps related to fftshift?
        filt_j = np.concatenate([filt[:int(sig_length/2)],
            [filt[int(sig_length / 2)] / 2 + filt[int(-sig_length / 2)] / 2],
            filt[int(-sig_length / 2 + 1):]], axis=0) # filt_j's length is identical to sig_length
        filt_j = filt_j[np.newaxis, :]
        yf = xf * np.tile(filt_j, (n_data, 1)) # FIXME: for 1 signal, a singleton dim added, resulting in yf being rank 2 array. consider refactoring
        print("\nfilter is array")
        print("filt_j:{}".format(filt_j))
        print("yf:{}".format(yf))
    
    # calculate the downsampling factor with respect to yf
    dsj = int(ds + np.round(np.log2(yf.shape[1] / sig_length)))
    print("dsj:{}".format(dsj))
    if dsj > 0:
        # actually downsample, so periodize in Fourier
        yf_ds = np.reshape(yf, [n_data, int(2**dsj), int(np.round(yf.shape[1]/2**dsj))]).sum(axis=1)
    elif dsj < 0:
        # upsample, so zero-pad in Fourier
        # note that this only happens for fourier_truncated filters, since otherwise
        # filter sizes are always the same as the signal size
        # also, we have to do one-sided padding since otherwise we might break 
        # continuity of Fourier transform
        yf_ds = np.concatenate(yf, np.zeros(yf.shape[0], (2**(-dsj)-1)*yf.shape[1]), axis=1) # FIXME: not sure
    else:
        yf_ds = yf
    
    if isinstance(filt, dict) and filt['type'] == 'fourier_truncated' and filt['recenter']:
        # result has been shifted in frequency so that the zero fre-
        # quency is actually at -filt.start+1
        yf_ds = np.roll(yf_ds, filt['start']-1, axis=1)

    y_ds = np.fft.ifft(yf_ds) / 2**(ds/2) # ifft default axis=-1

    return y_ds





def dyadic_freq_1d(filter_options):
    pass

