import numpy as np

def calculate_atr(candles, period=14):
    if len(candles) < period + 1:
        return 0.0010  # Fallback ATR if insufficient candles
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]['high']
        l = candles[i]['low']
        cp = candles[i-1]['close']
        tr = max(h - l, abs(h - cp), abs(l - cp))
        trs.append(tr)
    return float(np.mean(trs[-period:]))

def detect_key_levels(d1_candles, atr):
    """
    Identifies Fresh, Historical, and Disrespected Key Levels (A-shape, V-shape, OCL)
    """
    levels = []
    lookback = min(60, len(d1_candles) - 3)
    
    for i in range(len(d1_candles) - lookback, len(d1_candles) - 1):
        c_prev = d1_candles[i-1]
        c_curr = d1_candles[i]
        c_next = d1_candles[i+1]
        
        # A-Shape (Sell Zone)
        if c_curr['close'] > c_prev['close'] and c_next['close'] < c_curr['close']:
            levels.append({
                'price': c_curr['high'],
                'type': 'A-Shape',
                'zone_top': c_curr['high'],
                'zone_bot': max(c_curr['open'], c_curr['close']),
                'index': i
            })
            
        # V-Shape (Buy Zone)
        elif c_curr['close'] < c_prev['close'] and c_next['close'] > c_curr['close']:
            levels.append({
                'price': c_curr['low'],
                'type': 'V-Shape',
                'zone_top': min(c_curr['open'], c_curr['close']),
                'zone_bot': c_curr['low'],
                'index': i
            })
            
        # Open-Close Level (OCL)
        elif (c_curr['close'] > c_curr['open'] and c_prev['close'] > c_prev['open']) or \
             (c_curr['close'] < c_curr['open'] and c_prev['close'] < c_prev['open']):
            levels.append({
                'price': c_curr['close'],
                'type': 'OCL',
                'zone_top': max(c_curr['close'], c_prev['open']),
                'zone_bot': min(c_curr['close'], c_prev['open']),
                'index': i
            })
            
    return levels

def evaluate_drd(d1_candles, levels, atr):
    """
    Evaluates Daily Rejection Day (DRD) and scores out of 5
    """
    if not d1_candles or not levels:
        return None
        
    latest = d1_candles[-1]
    prev = d1_candles[-2]
    tolerance = atr * 0.25
    
    best_drd = None
    
    for lvl in levels:
        touched = (latest['high'] >= (lvl['zone_bot'] - tolerance)) and \
                  (latest['low'] <= (lvl['zone_top'] + tolerance))
                  
        if not touched:
            continue
            
        # Bearish Rejection
        if latest['high'] >= lvl['zone_bot'] and latest['close'] < lvl['zone_top']:
            sweep = latest['high'] > prev['high']
            score = 2  # +2 Level Quality (Fresh/Valid)
            score += 2 if (latest['high'] - latest['close']) >= (latest['high'] - latest['low']) * 0.4 else 1
            score += 1 if sweep else 0
            
            drd_type = "Strong" if score >= 5 else ("Medium" if score >= 3 else "Weak")
            if score >= 3:
                best_drd = {
                    'bias': 'Bearish',
                    'score': score,
                    'grade': drd_type,
                    'level': lvl,
                    'pd_sweep': sweep
                }
                
        # Bullish Rejection
        elif latest['low'] <= lvl['zone_top'] and latest['close'] > lvl['zone_bot']:
            sweep = latest['low'] < prev['low']
            score = 2  # +2 Level Quality
            score += 2 if (latest['close'] - latest['low']) >= (latest['high'] - latest['low']) * 0.4 else 1
            score += 1 if sweep else 0
            
            drd_type = "Strong" if score >= 5 else ("Medium" if score >= 3 else "Weak")
            if score >= 3:
                best_drd = {
                    'bias': 'Bullish',
                    'score': score,
                    'grade': drd_type,
                    'level': lvl,
                    'pd_sweep': sweep
                }
                
    return best_drd
      
