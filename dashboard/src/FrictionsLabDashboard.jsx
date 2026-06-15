import React, { useState, useMemo } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ScatterChart, Scatter, ZAxis, ReferenceLine, Cell,
} from "recharts";
import { Activity, AlertTriangle, Layers, TrendingUp, Gauge } from "lucide-react";

const DATA = 
{"data_quality":[{"metric":"total_contracts","value":42.0},{"metric":"retained_contracts","value":37.0},{"metric":"excluded_contracts","value":5.0},{"metric":"excluded_share","value":0.119},{"metric":"unique_expiries","value":3.0},{"metric":"median_spread_pct_retained","value":0.0882},{"metric":"mean_spread_pct_retained","value":0.0805},{"metric":"median_days_to_expiry_retained","value":35.3333}],"exclusion_reasons":[{"exclusion_reason":"retained","contract_count":37,"share_of_contracts":0.881},{"exclusion_reason":"zero bid","contract_count":1,"share_of_contracts":0.0238},{"exclusion_reason":"crossed market","contract_count":1,"share_of_contracts":0.0238},{"exclusion_reason":"missing bid/ask","contract_count":1,"share_of_contracts":0.0238},{"exclusion_reason":"wide spread","contract_count":1,"share_of_contracts":0.0238},{"exclusion_reason":"low liquidity","contract_count":1,"share_of_contracts":0.0238}],"iv_quotes":[{"contractSymbol":"SPY20260621C00540000","expiration":"2026-06-21","option_type":"call","strike":540.0,"log_moneyness":-0.105361,"moneyness":1.111111,"days_to_expiry":7.333322,"IV_bid":NaN,"IV_mid":NaN,"IV_ask":NaN,"IV_range":NaN,"IV_relative_range":NaN,"moneyness_bucket":"far_below_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"very_wide_spread","spread_pct":2.0,"is_excluded":true},{"contractSymbol":"SPY20260621P00540000","expiration":"2026-06-21","option_type":"put","strike":540.0,"log_moneyness":-0.105361,"moneyness":1.111111,"days_to_expiry":7.333322,"IV_bid":0.806784,"IV_mid":0.826238,"IV_ask":0.845324,"IV_range":0.038539,"IV_relative_range":0.046644,"moneyness_bucket":"far_below_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"wide_spread","spread_pct":0.124242,"is_excluded":false},{"contractSymbol":"SPY20260621C00560000","expiration":"2026-06-21","option_type":"call","strike":560.0,"log_moneyness":-0.068993,"moneyness":1.071429,"days_to_expiry":7.333322,"IV_bid":0.571609,"IV_mid":0.664122,"IV_ask":0.749911,"IV_range":0.178303,"IV_relative_range":0.268479,"moneyness_bucket":"below_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.092243,"is_excluded":false},{"contractSymbol":"SPY20260621P00560000","expiration":"2026-06-21","option_type":"put","strike":560.0,"log_moneyness":-0.068993,"moneyness":1.071429,"days_to_expiry":7.333322,"IV_bid":0.668121,"IV_mid":0.682082,"IV_ask":0.695897,"IV_range":0.027775,"IV_relative_range":0.040721,"moneyness_bucket":"below_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.090909,"is_excluded":false},{"contractSymbol":"SPY20260621C00580000","expiration":"2026-06-21","option_type":"call","strike":580.0,"log_moneyness":-0.033902,"moneyness":1.034483,"days_to_expiry":7.333322,"IV_bid":0.468339,"IV_mid":0.498038,"IV_ask":0.527314,"IV_range":0.058975,"IV_relative_range":0.118415,"moneyness_bucket":"slightly_below_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.060417,"is_excluded":false},{"contractSymbol":"SPY20260621P00580000","expiration":"2026-06-21","option_type":"put","strike":580.0,"log_moneyness":-0.033902,"moneyness":1.034483,"days_to_expiry":7.333322,"IV_bid":NaN,"IV_mid":NaN,"IV_ask":NaN,"IV_range":NaN,"IV_relative_range":NaN,"moneyness_bucket":"slightly_below_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"tight_spread","spread_pct":-0.029744,"is_excluded":true},{"contractSymbol":"SPY20260621C00600000","expiration":"2026-06-21","option_type":"call","strike":600.0,"log_moneyness":0.0,"moneyness":1.0,"days_to_expiry":7.333322,"IV_bid":0.28044,"IV_mid":0.284866,"IV_ask":0.289292,"IV_range":0.008852,"IV_relative_range":0.031075,"moneyness_bucket":"near_atm","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.030303,"is_excluded":false},{"contractSymbol":"SPY20260621P00600000","expiration":"2026-06-21","option_type":"put","strike":600.0,"log_moneyness":0.0,"moneyness":1.0,"days_to_expiry":7.333322,"IV_bid":0.294653,"IV_mid":0.299079,"IV_ask":0.303505,"IV_range":0.008852,"IV_relative_range":0.029598,"moneyness_bucket":"near_atm","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.030303,"is_excluded":false},{"contractSymbol":"SPY20260621C00620000","expiration":"2026-06-21","option_type":"call","strike":620.0,"log_moneyness":0.03279,"moneyness":0.967742,"days_to_expiry":7.333322,"IV_bid":0.478513,"IV_mid":0.486934,"IV_ask":0.495324,"IV_range":0.016811,"IV_relative_range":0.034524,"moneyness_bucket":"slightly_above_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.059091,"is_excluded":false},{"contractSymbol":"SPY20260621P00620000","expiration":"2026-06-21","option_type":"put","strike":620.0,"log_moneyness":0.03279,"moneyness":0.967742,"days_to_expiry":7.333322,"IV_bid":0.475191,"IV_mid":0.502969,"IV_ask":0.530442,"IV_range":0.05525,"IV_relative_range":0.109848,"moneyness_bucket":"slightly_above_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.059722,"is_excluded":false},{"contractSymbol":"SPY20260621C00640000","expiration":"2026-06-21","option_type":"call","strike":640.0,"log_moneyness":0.064539,"moneyness":0.9375,"days_to_expiry":7.333322,"IV_bid":0.61699,"IV_mid":0.629601,"IV_ask":0.642084,"IV_range":0.025094,"IV_relative_range":0.039858,"moneyness_bucket":"above_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.088312,"is_excluded":false},{"contractSymbol":"SPY20260621P00640000","expiration":"2026-06-21","option_type":"put","strike":640.0,"log_moneyness":0.064539,"moneyness":0.9375,"days_to_expiry":7.333322,"IV_bid":0.569487,"IV_mid":0.648419,"IV_ask":0.72292,"IV_range":0.153433,"IV_relative_range":0.236627,"moneyness_bucket":"above_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"moderate_spread","spread_pct":0.08805,"is_excluded":false},{"contractSymbol":"SPY20260621C00660000","expiration":"2026-06-21","option_type":"call","strike":660.0,"log_moneyness":0.09531,"moneyness":0.909091,"days_to_expiry":7.333322,"IV_bid":NaN,"IV_mid":NaN,"IV_ask":NaN,"IV_range":NaN,"IV_relative_range":NaN,"moneyness_bucket":"above_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"very_wide_spread","spread_pct":NaN,"is_excluded":true},{"contractSymbol":"SPY20260621P00660000","expiration":"2026-06-21","option_type":"put","strike":660.0,"log_moneyness":0.09531,"moneyness":0.909091,"days_to_expiry":7.333322,"IV_bid":0.583305,"IV_mid":0.762028,"IV_ask":0.911727,"IV_range":0.328422,"IV_relative_range":0.430983,"moneyness_bucket":"above_spot","expiry_bucket":"8_to_30_days","liquidity_bucket":"wide_spread","spread_pct":0.115916,"is_excluded":false},{"contractSymbol":"SPY20260719C00540000","expiration":"2026-07-19","option_type":"call","strike":540.0,"log_moneyness":-0.105361,"moneyness":1.111111,"days_to_expiry":35.333322,"IV_bid":0.357215,"IV_mid":0.450702,"IV_ask":0.533246,"IV_range":0.176031,"IV_relative_range":0.390571,"moneyness_bucket":"far_below_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"wide_spread","spread_pct":0.124722,"is_excluded":false},{"contractSymbol":"SPY20260719P00540000","expiration":"2026-07-19","option_type":"put","strike":540.0,"log_moneyness":-0.105361,"moneyness":1.111111,"days_to_expiry":35.333322,"IV_bid":0.476021,"IV_mid":0.48992,"IV_ask":0.503621,"IV_range":0.0276,"IV_relative_range":0.056336,"moneyness_bucket":"far_below_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"wide_spread","spread_pct":0.125,"is_excluded":false},{"contractSymbol":"SPY20260719C00560000","expiration":"2026-07-19","option_type":"call","strike":560.0,"log_moneyness":-0.068993,"moneyness":1.071429,"days_to_expiry":35.333322,"IV_bid":0.347902,"IV_mid":0.390421,"IV_ask":0.431328,"IV_range":0.083425,"IV_relative_range":0.213681,"moneyness_bucket":"below_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.092222,"is_excluded":false},{"contractSymbol":"SPY20260719P00560000","expiration":"2026-07-19","option_type":"put","strike":560.0,"log_moneyness":-0.068993,"moneyness":1.071429,"days_to_expiry":35.333322,"IV_bid":0.41559,"IV_mid":0.426023,"IV_ask":0.436379,"IV_range":0.020789,"IV_relative_range":0.048798,"moneyness_bucket":"below_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.091429,"is_excluded":false},{"contractSymbol":"SPY20260719C00580000","expiration":"2026-07-19","option_type":"call","strike":580.0,"log_moneyness":-0.033902,"moneyness":1.034483,"days_to_expiry":35.333322,"IV_bid":0.301599,"IV_mid":0.317731,"IV_ask":0.333746,"IV_range":0.032147,"IV_relative_range":0.101177,"moneyness_bucket":"slightly_below_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.060556,"is_excluded":false},{"contractSymbol":"SPY20260719P00580000","expiration":"2026-07-19","option_type":"put","strike":580.0,"log_moneyness":-0.033902,"moneyness":1.034483,"days_to_expiry":35.333322,"IV_bid":0.343539,"IV_mid":0.350535,"IV_ask":0.357514,"IV_range":0.013974,"IV_relative_range":0.039866,"moneyness_bucket":"slightly_below_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.06,"is_excluded":false},{"contractSymbol":"SPY20260719C00600000","expiration":"2026-07-19","option_type":"call","strike":600.0,"log_moneyness":0.0,"moneyness":1.0,"days_to_expiry":35.333322,"IV_bid":NaN,"IV_mid":NaN,"IV_ask":NaN,"IV_range":NaN,"IV_relative_range":NaN,"moneyness_bucket":"near_atm","expiry_bucket":"31_to_90_days","liquidity_bucket":"very_wide_spread","spread_pct":1.111111,"is_excluded":true},{"contractSymbol":"SPY20260719P00600000","expiration":"2026-07-19","option_type":"put","strike":600.0,"log_moneyness":0.0,"moneyness":1.0,"days_to_expiry":35.333322,"IV_bid":0.253965,"IV_mid":0.257606,"IV_ask":0.261246,"IV_range":0.007282,"IV_relative_range":0.028267,"moneyness_bucket":"near_atm","expiry_bucket":"31_to_90_days","liquidity_bucket":"tight_spread","spread_pct":0.03,"is_excluded":false},{"contractSymbol":"SPY20260719C00620000","expiration":"2026-07-19","option_type":"call","strike":620.0,"log_moneyness":0.03279,"moneyness":0.967742,"days_to_expiry":35.333322,"IV_bid":0.308194,"IV_mid":0.314846,"IV_ask":0.321486,"IV_range":0.013292,"IV_relative_range":0.042219,"moneyness_bucket":"slightly_above_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.06,"is_excluded":false},{"contractSymbol":"SPY20260719P00620000","expiration":"2026-07-19","option_type":"put","strike":620.0,"log_moneyness":0.03279,"moneyness":0.967742,"days_to_expiry":35.333322,"IV_bid":0.333142,"IV_mid":0.347867,"IV_ask":0.362549,"IV_range":0.029407,"IV_relative_range":0.084536,"moneyness_bucket":"slightly_above_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.059444,"is_excluded":false},{"contractSymbol":"SPY20260719C00640000","expiration":"2026-07-19","option_type":"call","strike":640.0,"log_moneyness":0.064539,"moneyness":0.9375,"days_to_expiry":35.333322,"IV_bid":0.36852,"IV_mid":0.377798,"IV_ask":0.387016,"IV_range":0.018495,"IV_relative_range":0.048956,"moneyness_bucket":"above_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.088571,"is_excluded":false},{"contractSymbol":"SPY20260719P00640000","expiration":"2026-07-19","option_type":"put","strike":640.0,"log_moneyness":0.064539,"moneyness":0.9375,"days_to_expiry":35.333322,"IV_bid":0.379165,"IV_mid":0.414237,"IV_ask":0.44867,"IV_range":0.069505,"IV_relative_range":0.167791,"moneyness_bucket":"above_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"moderate_spread","spread_pct":0.088148,"is_excluded":false},{"contractSymbol":"SPY20260719C00660000","expiration":"2026-07-19","option_type":"call","strike":660.0,"log_moneyness":0.09531,"moneyness":0.909091,"days_to_expiry":35.333322,"IV_bid":0.413426,"IV_mid":0.424774,"IV_ask":0.43598,"IV_range":0.022554,"IV_relative_range":0.053097,"moneyness_bucket":"above_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"wide_spread","spread_pct":0.115,"is_excluded":false},{"contractSymbol":"SPY20260719P00660000","expiration":"2026-07-19","option_type":"put","strike":660.0,"log_moneyness":0.09531,"moneyness":0.909091,"days_to_expiry":35.333322,"IV_bid":NaN,"IV_mid":NaN,"IV_ask":NaN,"IV_range":NaN,"IV_relative_range":NaN,"moneyness_bucket":"above_spot","expiry_bucket":"31_to_90_days","liquidity_bucket":"low_activity","spread_pct":0.115833,"is_excluded":true},{"contractSymbol":"SPY20260918C00540000","expiration":"2026-09-18","option_type":"call","strike":540.0,"log_moneyness":-0.105361,"moneyness":1.111111,"days_to_expiry":96.333322,"IV_bid":0.259826,"IV_mid":0.317579,"IV_ask":0.370334,"IV_range":0.110509,"IV_relative_range":0.347972,"moneyness_bucket":"far_below_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"wide_spread","spread_pct":0.124936,"is_excluded":false},{"contractSymbol":"SPY20260918P00540000","expiration":"2026-09-18","option_type":"put","strike":540.0,"log_moneyness":-0.105361,"moneyness":1.111111,"days_to_expiry":96.333322,"IV_bid":0.366124,"IV_mid":0.378197,"IV_ask":0.390139,"IV_range":0.024015,"IV_relative_range":0.063499,"moneyness_bucket":"far_below_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"wide_spread","spread_pct":0.124731,"is_excluded":false},{"contractSymbol":"SPY20260918C00560000","expiration":"2026-09-18","option_type":"call","strike":560.0,"log_moneyness":-0.068993,"moneyness":1.071429,"days_to_expiry":96.333322,"IV_bid":0.259204,"IV_mid":0.287511,"IV_ask":0.315037,"IV_range":0.055832,"IV_relative_range":0.194192,"moneyness_bucket":"below_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.092058,"is_excluded":false},{"contractSymbol":"SPY20260918P00560000","expiration":"2026-09-18","option_type":"put","strike":560.0,"log_moneyness":-0.068993,"moneyness":1.071429,"days_to_expiry":96.333322,"IV_bid":0.334424,"IV_mid":0.343856,"IV_ask":0.353236,"IV_range":0.018812,"IV_relative_range":0.054709,"moneyness_bucket":"below_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.092166,"is_excluded":false},{"contractSymbol":"SPY20260918C00580000","expiration":"2026-09-18","option_type":"call","strike":580.0,"log_moneyness":-0.033902,"moneyness":1.034483,"days_to_expiry":96.333322,"IV_bid":0.237333,"IV_mid":0.249407,"IV_ask":0.261414,"IV_range":0.024081,"IV_relative_range":0.096553,"moneyness_bucket":"slightly_below_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.060714,"is_excluded":false},{"contractSymbol":"SPY20260918P00580000","expiration":"2026-09-18","option_type":"put","strike":580.0,"log_moneyness":-0.033902,"moneyness":1.034483,"days_to_expiry":96.333322,"IV_bid":0.296219,"IV_mid":0.302743,"IV_ask":0.309256,"IV_range":0.013036,"IV_relative_range":0.043061,"moneyness_bucket":"slightly_below_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.060484,"is_excluded":false},{"contractSymbol":"SPY20260918C00600000","expiration":"2026-09-18","option_type":"call","strike":600.0,"log_moneyness":0.0,"moneyness":1.0,"days_to_expiry":96.333322,"IV_bid":0.197999,"IV_mid":0.201456,"IV_ask":0.204913,"IV_range":0.006914,"IV_relative_range":0.034322,"moneyness_bucket":"near_atm","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.030108,"is_excluded":false},{"contractSymbol":"SPY20260918P00600000","expiration":"2026-09-18","option_type":"put","strike":600.0,"log_moneyness":0.0,"moneyness":1.0,"days_to_expiry":96.333322,"IV_bid":0.249797,"IV_mid":0.253251,"IV_ask":0.256704,"IV_range":0.006907,"IV_relative_range":0.027272,"moneyness_bucket":"near_atm","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.030108,"is_excluded":false},{"contractSymbol":"SPY20260918C00620000","expiration":"2026-09-18","option_type":"call","strike":620.0,"log_moneyness":0.03279,"moneyness":0.967742,"days_to_expiry":96.333322,"IV_bid":0.244156,"IV_mid":0.250214,"IV_ask":0.256267,"IV_range":0.012111,"IV_relative_range":0.048403,"moneyness_bucket":"slightly_above_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.059677,"is_excluded":false},{"contractSymbol":"SPY20260918P00620000","expiration":"2026-09-18","option_type":"put","strike":620.0,"log_moneyness":0.03279,"moneyness":0.967742,"days_to_expiry":96.333322,"IV_bid":0.292498,"IV_mid":0.303343,"IV_ask":0.314182,"IV_range":0.021684,"IV_relative_range":0.071485,"moneyness_bucket":"slightly_above_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.059375,"is_excluded":false},{"contractSymbol":"SPY20260918C00640000","expiration":"2026-09-18","option_type":"call","strike":640.0,"log_moneyness":0.064539,"moneyness":0.9375,"days_to_expiry":96.333322,"IV_bid":0.276421,"IV_mid":0.284596,"IV_ask":0.292741,"IV_range":0.016321,"IV_relative_range":0.057347,"moneyness_bucket":"above_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.088479,"is_excluded":false},{"contractSymbol":"SPY20260918P00640000","expiration":"2026-09-18","option_type":"put","strike":640.0,"log_moneyness":0.064539,"moneyness":0.9375,"days_to_expiry":96.333322,"IV_bid":0.318331,"IV_mid":0.341074,"IV_ask":0.363685,"IV_range":0.045354,"IV_relative_range":0.132974,"moneyness_bucket":"above_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"moderate_spread","spread_pct":0.088169,"is_excluded":false},{"contractSymbol":"SPY20260918C00660000","expiration":"2026-09-18","option_type":"call","strike":660.0,"log_moneyness":0.09531,"moneyness":0.909091,"days_to_expiry":96.333322,"IV_bid":0.299282,"IV_mid":0.309069,"IV_ask":0.31877,"IV_range":0.019488,"IV_relative_range":0.063052,"moneyness_bucket":"above_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"wide_spread","spread_pct":0.116129,"is_excluded":false},{"contractSymbol":"SPY20260918P00660000","expiration":"2026-09-18","option_type":"put","strike":660.0,"log_moneyness":0.09531,"moneyness":0.909091,"days_to_expiry":96.333322,"IV_bid":0.330313,"IV_mid":0.370131,"IV_ask":0.409141,"IV_range":0.078828,"IV_relative_range":0.212974,"moneyness_bucket":"above_spot","expiry_bucket":"91_to_180_days","liquidity_bucket":"wide_spread","spread_pct":0.115776,"is_excluded":false}],"iv_by_expiry":[{"expiration":"2026-06-21","option_type":"call","contract_count":5,"mean_iv_mid":0.512712,"median_iv_mid":0.498038,"mean_iv_range":0.057607,"median_iv_range":0.025094,"max_iv_range":0.178303,"mean_iv_relative_range":0.09847,"median_iv_relative_range":0.039858},{"expiration":"2026-06-21","option_type":"put","contract_count":6,"mean_iv_mid":0.620136,"median_iv_mid":0.665251,"mean_iv_range":0.102045,"median_iv_range":0.046895,"max_iv_range":0.328422,"mean_iv_relative_range":0.14907,"median_iv_relative_range":0.078246},{"expiration":"2026-07-19","option_type":"call","contract_count":6,"mean_iv_mid":0.379379,"median_iv_mid":0.384109,"mean_iv_range":0.057658,"median_iv_range":0.027351,"max_iv_range":0.176031,"mean_iv_relative_range":0.141617,"median_iv_relative_range":0.077137},{"expiration":"2026-07-19","option_type":"put","contract_count":6,"mean_iv_mid":0.381031,"median_iv_mid":0.382386,"mean_iv_range":0.028093,"median_iv_range":0.024195,"max_iv_range":0.069505,"mean_iv_relative_range":0.070932,"median_iv_relative_range":0.052567},{"expiration":"2026-09-18","option_type":"call","contract_count":7,"mean_iv_mid":0.271405,"median_iv_mid":0.284596,"mean_iv_range":0.035037,"median_iv_range":0.019488,"max_iv_range":0.110509,"mean_iv_relative_range":0.120263,"median_iv_relative_range":0.063052},{"expiration":"2026-09-18","option_type":"put","contract_count":7,"mean_iv_mid":0.327514,"median_iv_mid":0.341074,"mean_iv_range":0.029805,"median_iv_range":0.021684,"max_iv_range":0.078828,"mean_iv_relative_range":0.086568,"median_iv_relative_range":0.063499}],"iv_by_moneyness":[{"moneyness_bucket":"far_below_spot","option_type":"call","contract_count":2,"mean_iv_mid":0.38414,"median_iv_mid":0.38414,"mean_iv_range":0.14327,"median_iv_range":0.14327,"max_iv_range":0.176031,"mean_iv_relative_range":0.369271,"median_iv_relative_range":0.369271},{"moneyness_bucket":"below_spot","option_type":"call","contract_count":3,"mean_iv_mid":0.447351,"median_iv_mid":0.390421,"mean_iv_range":0.105854,"median_iv_range":0.083425,"max_iv_range":0.178303,"mean_iv_relative_range":0.225451,"median_iv_relative_range":0.213681},{"moneyness_bucket":"above_spot","option_type":"put","contract_count":5,"mean_iv_mid":0.507178,"median_iv_mid":0.414237,"mean_iv_range":0.135109,"median_iv_range":0.078828,"max_iv_range":0.328422,"mean_iv_relative_range":0.23627,"median_iv_relative_range":0.212974},{"moneyness_bucket":"slightly_below_spot","option_type":"call","contract_count":3,"mean_iv_mid":0.355059,"median_iv_mid":0.317731,"mean_iv_range":0.038401,"median_iv_range":0.032147,"max_iv_range":0.058975,"mean_iv_relative_range":0.105382,"median_iv_relative_range":0.101177},{"moneyness_bucket":"slightly_above_spot","option_type":"put","contract_count":3,"mean_iv_mid":0.384726,"median_iv_mid":0.347867,"mean_iv_range":0.035447,"median_iv_range":0.029407,"max_iv_range":0.05525,"mean_iv_relative_range":0.088623,"median_iv_relative_range":0.084536},{"moneyness_bucket":"far_below_spot","option_type":"put","contract_count":3,"mean_iv_mid":0.564785,"median_iv_mid":0.48992,"mean_iv_range":0.030052,"median_iv_range":0.0276,"max_iv_range":0.038539,"mean_iv_relative_range":0.055493,"median_iv_relative_range":0.056336},{"moneyness_bucket":"above_spot","option_type":"call","contract_count":5,"mean_iv_mid":0.405168,"median_iv_mid":0.377798,"mean_iv_range":0.020391,"median_iv_range":0.019488,"max_iv_range":0.025094,"mean_iv_relative_range":0.052462,"median_iv_relative_range":0.053097},{"moneyness_bucket":"below_spot","option_type":"put","contract_count":3,"mean_iv_mid":0.483987,"median_iv_mid":0.426023,"mean_iv_range":0.022459,"median_iv_range":0.020789,"max_iv_range":0.027775,"mean_iv_relative_range":0.048076,"median_iv_relative_range":0.048798},{"moneyness_bucket":"slightly_above_spot","option_type":"call","contract_count":3,"mean_iv_mid":0.350665,"median_iv_mid":0.314846,"mean_iv_range":0.014071,"median_iv_range":0.013292,"max_iv_range":0.016811,"mean_iv_relative_range":0.041715,"median_iv_relative_range":0.042219},{"moneyness_bucket":"slightly_below_spot","option_type":"put","contract_count":2,"mean_iv_mid":0.326639,"median_iv_mid":0.326639,"mean_iv_range":0.013505,"median_iv_range":0.013505,"max_iv_range":0.013974,"mean_iv_relative_range":0.041464,"median_iv_relative_range":0.041464},{"moneyness_bucket":"near_atm","option_type":"call","contract_count":2,"mean_iv_mid":0.243161,"median_iv_mid":0.243161,"mean_iv_range":0.007883,"median_iv_range":0.007883,"max_iv_range":0.008852,"mean_iv_relative_range":0.032699,"median_iv_relative_range":0.032699},{"moneyness_bucket":"near_atm","option_type":"put","contract_count":3,"mean_iv_mid":0.269978,"median_iv_mid":0.257606,"mean_iv_range":0.00768,"median_iv_range":0.007282,"max_iv_range":0.008852,"mean_iv_relative_range":0.028379,"median_iv_relative_range":0.028267}],"greeks":[{"contractSymbol":"SPY20260621C00540000","expiration":"2026-06-21","option_type":"call","strike":540.0,"log_moneyness":-0.105361,"days_to_expiry":7.333322,"Delta_mid":NaN,"Gamma_mid":NaN,"Vega_mid":NaN,"Theta_mid":NaN,"Delta_range":NaN,"Gamma_range":NaN,"Vega_range":NaN,"Theta_range":NaN,"is_excluded":true},{"contractSymbol":"SPY20260621P00540000","expiration":"2026-06-21","option_type":"put","strike":540.0,"log_moneyness":-0.105361,"days_to_expiry":7.333322,"Delta_mid":-0.167186,"Gamma_mid":0.003564,"Vega_mid":21.284287,"Theta_mid":-433.672787,"Delta_range":0.00991,"Gamma_range":3e-05,"Vega_range":0.813762,"Theta_range":36.883905,"is_excluded":false},{"contractSymbol":"SPY20260621C00560000","expiration":"2026-06-21","option_type":"call","strike":560.0,"log_moneyness":-0.068993,"days_to_expiry":7.333322,"Delta_mid":0.784871,"Gamma_mid":0.005177,"Vega_mid":24.849835,"Theta_mid":-427.918376,"Delta_range":0.055394,"Gamma_range":0.000601,"Vega_range":3.78461,"Theta_range":169.420198,"is_excluded":false},{"contractSymbol":"SPY20260621P00560000","expiration":"2026-06-21","option_type":"put","strike":560.0,"log_moneyness":-0.068993,"days_to_expiry":7.333322,"Delta_mid":-0.220504,"Gamma_mid":0.005113,"Vega_mid":25.206087,"Theta_mid":-422.55569,"Delta_range":0.008138,"Gamma_range":0.0001,"Vega_range":0.533332,"Theta_range":26.264265,"is_excluded":false},{"contractSymbol":"SPY20260621C00580000","expiration":"2026-06-21","option_type":"call","strike":580.0,"log_moneyness":-0.033902,"days_to_expiry":7.333322,"Delta_mid":0.700925,"Gamma_mid":0.0082,"Vega_mid":29.518468,"Theta_mid":-381.783521,"Delta_range":0.018836,"Gamma_range":0.000738,"Vega_range":0.846912,"Theta_range":53.275884,"is_excluded":false},{"contractSymbol":"SPY20260621P00580000","expiration":"2026-06-21","option_type":"put","strike":580.0,"log_moneyness":-0.033902,"days_to_expiry":7.333322,"Delta_mid":NaN,"Gamma_mid":NaN,"Vega_mid":NaN,"Theta_mid":NaN,"Delta_range":NaN,"Gamma_range":NaN,"Vega_range":NaN,"Theta_range":NaN,"is_excluded":true},{"contractSymbol":"SPY20260621C00600000","expiration":"2026-06-21","option_type":"call","strike":600.0,"log_moneyness":0.0,"days_to_expiry":7.333322,"Delta_mid":0.515985,"Gamma_mid":0.016459,"Vega_mid":33.889704,"Theta_mid":-252.406323,"Delta_range":3e-06,"Gamma_range":0.000512,"Vega_range":1.2e-05,"Theta_range":7.459041,"is_excluded":false},{"contractSymbol":"SPY20260621P00600000","expiration":"2026-06-21","option_type":"put","strike":600.0,"log_moneyness":0.0,"days_to_expiry":7.333322,"Delta_mid":-0.483991,"Gamma_mid":0.015677,"Vega_mid":33.88962,"Theta_mid":-240.401488,"Delta_range":2.6e-05,"Gamma_range":0.000464,"Vega_range":9e-05,"Theta_range":7.458986,"is_excluded":false},{"contractSymbol":"SPY20260621C00620000","expiration":"2026-06-21","option_type":"call","strike":620.0,"log_moneyness":0.03279,"days_to_expiry":7.333322,"Delta_mid":0.333924,"Gamma_mid":0.008789,"Vega_mid":30.933806,"Theta_mid":-382.775692,"Delta_range":0.006259,"Gamma_range":0.000239,"Vega_range":0.228394,"Theta_range":15.847923,"is_excluded":false},{"contractSymbol":"SPY20260621P00620000","expiration":"2026-06-21","option_type":"put","strike":620.0,"log_moneyness":0.03279,"days_to_expiry":7.333322,"Delta_mid":-0.660265,"Gamma_mid":0.008566,"Vega_mid":31.141852,"Theta_mid":-373.073912,"Delta_range":0.019545,"Gamma_range":0.000753,"Vega_range":0.688909,"Theta_range":51.836114,"is_excluded":false},{"contractSymbol":"SPY20260621C00640000","expiration":"2026-06-21","option_type":"call","strike":640.0,"log_moneyness":0.064539,"days_to_expiry":7.333322,"Delta_mid":0.251484,"Gamma_mid":0.005955,"Vega_mid":27.101288,"Theta_mid":-430.654836,"Delta_range":0.009647,"Gamma_range":0.000117,"Vega_range":0.549615,"Theta_range":25.752483,"is_excluded":false},{"contractSymbol":"SPY20260621P00640000","expiration":"2026-06-21","option_type":"put","strike":640.0,"log_moneyness":0.064539,"days_to_expiry":7.333322,"Delta_mid":-0.741429,"Gamma_mid":0.005867,"Vega_mid":27.498156,"Theta_mid":-424.3342,"Delta_range":0.057225,"Gamma_range":0.000707,"Vega_range":3.203621,"Theta_range":156.742678,"is_excluded":false},{"contractSymbol":"SPY20260621C00660000","expiration":"2026-06-21","option_type":"call","strike":660.0,"log_moneyness":0.09531,"days_to_expiry":7.333322,"Delta_mid":NaN,"Gamma_mid":NaN,"Vega_mid":NaN,"Theta_mid":NaN,"Delta_range":NaN,"Gamma_range":NaN,"Vega_range":NaN,"Theta_range":NaN,"is_excluded":true},{"contractSymbol":"SPY20260621P00660000","expiration":"2026-06-21","option_type":"put","strike":660.0,"log_moneyness":0.09531,"days_to_expiry":7.333322,"Delta_mid":-0.794255,"Gamma_mid":0.004395,"Vega_mid":24.20766,"Theta_mid":-437.66595,"Delta_range":0.117194,"Gamma_range":0.000262,"Vega_range":8.675189,"Theta_range":350.604579,"is_excluded":false},{"contractSymbol":"SPY20260719C00540000","expiration":"2026-07-19","option_type":"call","strike":540.0,"log_moneyness":-0.105361,"days_to_expiry":35.333322,"Delta_mid":0.802143,"Gamma_mid":0.003307,"Vega_mid":51.907138,"Theta_mid":-137.289745,"Delta_range":0.079715,"Gamma_range":0.000444,"Vega_range":13.144224,"Theta_range":73.450579,"is_excluded":false},{"contractSymbol":"SPY20260719P00540000","expiration":"2026-07-19","option_type":"put","strike":540.0,"log_moneyness":-0.105361,"days_to_expiry":35.333322,"Delta_mid":-0.213882,"Gamma_mid":0.003186,"Vega_mid":54.36218,"Theta_mid":-132.043553,"Delta_range":0.010522,"Gamma_range":8.8e-05,"Vega_range":1.558329,"Theta_range":11.38301,"is_excluded":false},{"contractSymbol":"SPY20260719C00560000","expiration":"2026-07-19","option_type":"call","strike":560.0,"log_moneyness":-0.068993,"days_to_expiry":35.333322,"Delta_mid":0.745612,"Gamma_mid":0.004402,"Vega_mid":59.848755,"Theta_mid":-136.505976,"Delta_range":0.037394,"Gamma_range":0.000602,"Vega_range":4.661982,"Theta_range":33.935276,"is_excluded":false},{"contractSymbol":"SPY20260719P00560000","expiration":"2026-07-19","option_type":"put","strike":560.0,"log_moneyness":-0.068993,"days_to_expiry":35.333322,"Delta_mid":-0.268901,"Gamma_mid":0.00415,"Vega_mid":61.577689,"Theta_mid":-128.57767,"Delta_range":0.007792,"Gamma_range":0.000142,"Vega_range":0.896474,"Theta_range":8.350374,"is_excluded":false},{"contractSymbol":"SPY20260719C00580000","expiration":"2026-07-19","option_type":"call","strike":580.0,"log_moneyness":-0.033902,"days_to_expiry":35.333322,"Delta_mid":0.666992,"Gamma_mid":0.00613,"Vega_mid":67.827294,"Theta_mid":-125.956123,"Delta_range":0.012274,"Gamma_range":0.000532,"Vega_range":0.990896,"Theta_range":12.508777,"is_excluded":false},{"contractSymbol":"SPY20260719P00580000","expiration":"2026-07-19","option_type":"put","strike":580.0,"log_moneyness":-0.033902,"days_to_expiry":35.333322,"Delta_mid":-0.344227,"Gamma_mid":0.005628,"Vega_mid":68.698738,"Theta_mid":-115.565892,"Delta_range":0.004286,"Gamma_range":0.000198,"Vega_range":0.320833,"Theta_range":5.401654,"is_excluded":false},{"contractSymbol":"SPY20260719C00600000","expiration":"2026-07-19","option_type":"call","strike":600.0,"log_moneyness":0.0,"days_to_expiry":35.333322,"Delta_mid":NaN,"Gamma_mid":NaN,"Vega_mid":NaN,"Theta_mid":NaN,"Delta_range":NaN,"Gamma_range":NaN,"Vega_range":NaN,"Theta_range":NaN,"is_excluded":true},{"contractSymbol":"SPY20260719P00600000","expiration":"2026-07-19","option_type":"put","strike":600.0,"log_moneyness":0.0,"days_to_expiry":35.333322,"Delta_mid":-0.464797,"Gamma_mid":0.008266,"Vega_mid":74.158889,"Theta_mid":-86.865124,"Delta_range":9.3e-05,"Gamma_range":0.000234,"Vega_range":0.001527,"Theta_range":2.769272,"is_excluded":false},{"contractSymbol":"SPY20260719C00620000","expiration":"2026-07-19","option_type":"call","strike":620.0,"log_moneyness":0.03279,"days_to_expiry":35.333322,"Delta_mid":0.402699,"Gamma_mid":0.006587,"Vega_mid":72.223459,"Theta_mid":-126.55581,"Delta_range":0.005628,"Gamma_range":0.000255,"Vega_range":0.258875,"Theta_range":5.479627,"is_excluded":false},{"contractSymbol":"SPY20260719P00620000","expiration":"2026-07-19","option_type":"put","strike":620.0,"log_moneyness":0.03279,"days_to_expiry":35.333322,"Delta_mid":-0.584414,"Gamma_mid":0.006007,"Vega_mid":72.776023,"Theta_mid":-115.385097,"Delta_range":0.010611,"Gamma_range":0.000474,"Vega_range":0.423127,"Theta_range":11.989262,"is_excluded":false},{"contractSymbol":"SPY20260719C00640000","expiration":"2026-07-19","option_type":"call","strike":640.0,"log_moneyness":0.064539,"days_to_expiry":35.333322,"Delta_mid":0.323635,"Gamma_mid":0.005096,"Vega_mid":67.049688,"Theta_mid":-138.135077,"Delta_range":0.01012,"Gamma_range":0.000184,"Vega_range":0.864739,"Theta_range":8.289887,"is_excluded":false},{"contractSymbol":"SPY20260719P00640000","expiration":"2026-07-19","option_type":"put","strike":640.0,"log_moneyness":0.064539,"days_to_expiry":35.333322,"Delta_mid":-0.657802,"Gamma_mid":0.004752,"Vega_mid":68.545897,"Theta_mid":-128.812293,"Delta_range":0.033183,"Gamma_range":0.000625,"Vega_range":2.538596,"Theta_range":30.603281,"is_excluded":false},{"contractSymbol":"SPY20260719C00660000","expiration":"2026-07-19","option_type":"call","strike":660.0,"log_moneyness":0.09531,"days_to_expiry":35.333322,"Delta_mid":0.265636,"Gamma_mid":0.004137,"Vega_mid":61.199162,"Theta_mid":-140.258096,"Delta_range":0.013209,"Gamma_range":0.000115,"Vega_range":1.544569,"Theta_range":10.783026,"is_excluded":false},{"contractSymbol":"SPY20260719P00660000","expiration":"2026-07-19","option_type":"put","strike":660.0,"log_moneyness":0.09531,"days_to_expiry":35.333322,"Delta_mid":NaN,"Gamma_mid":NaN,"Vega_mid":NaN,"Theta_mid":NaN,"Delta_range":NaN,"Gamma_range":NaN,"Vega_range":NaN,"Theta_range":NaN,"is_excluded":true},{"contractSymbol":"SPY20260918C00540000","expiration":"2026-09-18","option_type":"call","strike":540.0,"log_moneyness":-0.105361,"days_to_expiry":96.333322,"Delta_mid":0.785888,"Gamma_mid":0.002979,"Vega_mid":89.818411,"Theta_mid":-69.792823,"Delta_range":0.06575,"Gamma_range":0.00049,"Vega_range":16.53871,"Theta_range":26.268747,"is_excluded":false},{"contractSymbol":"SPY20260918P00540000","expiration":"2026-09-18","option_type":"put","strike":540.0,"log_moneyness":-0.105361,"days_to_expiry":96.333322,"Delta_mid":-0.243876,"Gamma_mid":0.002691,"Vega_mid":96.627769,"Theta_mid":-62.682359,"Delta_range":0.009961,"Gamma_range":0.000112,"Vega_range":2.131641,"Theta_range":5.592953,"is_excluded":false},{"contractSymbol":"SPY20260918C00560000","expiration":"2026-09-18","option_type":"call","strike":560.0,"log_moneyness":-0.068993,"days_to_expiry":96.333322,"Delta_mid":0.729908,"Gamma_mid":0.003733,"Vega_mid":101.901607,"Theta_mid":-70.591463,"Delta_range":0.030166,"Gamma_range":0.000518,"Vega_range":5.743318,"Theta_range":12.91546,"is_excluded":false},{"contractSymbol":"SPY20260918P00560000","expiration":"2026-09-18","option_type":"put","strike":560.0,"log_moneyness":-0.068993,"days_to_expiry":96.333322,"Delta_mid":-0.295037,"Gamma_mid":0.003257,"Vega_mid":106.324141,"Theta_mid":-61.360429,"Delta_range":0.006842,"Gamma_range":0.000143,"Vega_range":1.136604,"Theta_range":4.287615,"is_excluded":false},{"contractSymbol":"SPY20260918C00580000","expiration":"2026-09-18","option_type":"call","strike":580.0,"log_moneyness":-0.033902,"days_to_expiry":96.333322,"Delta_mid":0.659495,"Gamma_mid":0.00477,"Vega_mid":112.968772,"Theta_mid":-67.449429,"Delta_range":0.010046,"Gamma_range":0.000408,"Vega_range":1.275082,"Theta_range":5.407949,"is_excluded":false},{"contractSymbol":"SPY20260918P00580000","expiration":"2026-09-18","option_type":"put","strike":580.0,"log_moneyness":-0.033902,"days_to_expiry":96.333322,"Delta_mid":-0.358063,"Gamma_mid":0.004003,"Vega_mid":115.064141,"Theta_mid":-56.453085,"Delta_range":0.003349,"Gamma_range":0.000159,"Vega_range":0.375439,"Theta_range":2.918623,"is_excluded":false},{"contractSymbol":"SPY20260918C00600000","expiration":"2026-09-18","option_type":"call","strike":600.0,"log_moneyness":0.0,"days_to_expiry":96.333322,"Delta_mid":0.561077,"Gamma_mid":0.006351,"Vega_mid":121.485555,"Theta_mid":-58.74675,"Delta_range":0.00068,"Gamma_range":0.000216,"Vega_range":0.032223,"Theta_range":1.554816,"is_excluded":false},{"contractSymbol":"SPY20260918P00600000","expiration":"2026-09-18","option_type":"put","strike":600.0,"log_moneyness":0.0,"days_to_expiry":96.333322,"Delta_mid":-0.441903,"Gamma_mid":0.005058,"Vega_mid":121.623234,"Theta_mid":-46.670015,"Delta_range":0.000173,"Gamma_range":0.000138,"Vega_range":0.007805,"Theta_range":1.558424,"is_excluded":false},{"contractSymbol":"SPY20260918C00620000","expiration":"2026-09-18","option_type":"call","strike":620.0,"log_moneyness":0.03279,"days_to_expiry":96.333322,"Delta_mid":0.456671,"Gamma_mid":0.005144,"Vega_mid":122.203296,"Theta_mid":-67.934726,"Delta_range":0.004558,"Gamma_range":0.000243,"Vega_range":0.15297,"Theta_range":2.928414,"is_excluded":false},{"contractSymbol":"SPY20260918P00620000","expiration":"2026-09-18","option_type":"put","strike":620.0,"log_moneyness":0.03279,"days_to_expiry":96.333322,"Delta_mid":-0.52586,"Gamma_mid":0.004259,"Vega_mid":122.670676,"Theta_mid":-56.131013,"Delta_range":0.006285,"Gamma_range":0.0003,"Vega_range":0.125972,"Theta_range":5.159452,"is_excluded":false},{"contractSymbol":"SPY20260918C00640000","expiration":"2026-09-18","option_type":"call","strike":640.0,"log_moneyness":0.064539,"days_to_expiry":96.333322,"Delta_mid":0.383498,"Gamma_mid":0.004354,"Vega_mid":117.649318,"Theta_mid":-71.810878,"Delta_range":0.009694,"Gamma_range":0.000217,"Vega_range":0.886056,"Theta_range":4.273355,"is_excluded":false},{"contractSymbol":"SPY20260918P00640000","expiration":"2026-09-18","option_type":"put","strike":640.0,"log_moneyness":0.064539,"days_to_expiry":96.333322,"Delta_mid":-0.587313,"Gamma_mid":0.003705,"Vega_mid":119.972988,"Theta_mid":-61.010496,"Delta_range":0.02056,"Gamma_range":0.000451,"Vega_range":1.406653,"Theta_range":11.493773,"is_excluded":false},{"contractSymbol":"SPY20260918C00660000","expiration":"2026-09-18","option_type":"call","strike":660.0,"log_moneyness":0.09531,"days_to_expiry":96.333322,"Delta_mid":0.324684,"Gamma_mid":0.003778,"Vega_mid":110.858899,"Theta_mid":-72.002956,"Delta_range":0.013925,"Gamma_range":0.000172,"Vega_range":1.953134,"Theta_range":5.485794,"is_excluded":false},{"contractSymbol":"SPY20260918P00660000","expiration":"2026-09-18","option_type":"put","strike":660.0,"log_moneyness":0.09531,"days_to_expiry":96.333322,"Delta_mid":-0.637155,"Gamma_mid":0.003289,"Vega_mid":115.590578,"Theta_mid":-62.671893,"Delta_range":0.043596,"Gamma_range":0.00057,"Vega_range":4.784813,"Theta_range":21.249461,"is_excluded":false}],"short_expiry_summary":[{"dte_bucket":"8_to_14_DTE","option_type":"call","contract_count":5,"median_days_to_expiry":7.333322,"median_gamma":0.0082,"max_gamma":0.016459,"median_theta":-382.775692,"median_abs_theta":382.775692,"median_vega":29.518468,"median_iv_uncertainty":0.039858,"max_iv_uncertainty":0.268479,"median_spread_pct":0.060417,"max_spread_pct":0.092243},{"dte_bucket":"8_to_14_DTE","option_type":"put","contract_count":6,"median_days_to_expiry":7.333322,"median_gamma":0.00549,"max_gamma":0.015677,"median_theta":-423.444945,"median_abs_theta":423.444945,"median_vega":26.352122,"median_iv_uncertainty":0.078246,"max_iv_uncertainty":0.430983,"median_spread_pct":0.08948,"max_spread_pct":0.124242},{"dte_bucket":"31_to_60_DTE","option_type":"call","contract_count":6,"median_days_to_expiry":35.333322,"median_gamma":0.004749,"max_gamma":0.006587,"median_theta":-136.89786,"median_abs_theta":136.89786,"median_vega":64.124425,"median_iv_uncertainty":0.077137,"max_iv_uncertainty":0.390571,"median_spread_pct":0.090397,"max_spread_pct":0.124722},{"dte_bucket":"31_to_60_DTE","option_type":"put","contract_count":6,"median_days_to_expiry":35.333322,"median_gamma":0.00519,"max_gamma":0.008266,"median_theta":-122.071781,"median_abs_theta":122.071781,"median_vega":68.622318,"median_iv_uncertainty":0.052567,"max_iv_uncertainty":0.167791,"median_spread_pct":0.074074,"max_spread_pct":0.125}],"surface_diagnostics":[{"expiration":"2026-09-18","option_type":"put","total_quotes":7,"retained_quotes":7,"excluded_quotes":0,"complete_mid_iv_quotes":7,"median_spread_pct":0.0882,"median_iv_mid":0.3411,"median_iv_relative_range":0.0635,"min_log_moneyness":-0.1054,"max_log_moneyness":0.0953,"unique_strikes":7,"retention_rate":1.0,"iv_completion_rate":1.0,"log_moneyness_coverage":0.2007,"reliability_score":0.976},{"expiration":"2026-09-18","option_type":"call","total_quotes":7,"retained_quotes":7,"excluded_quotes":0,"complete_mid_iv_quotes":7,"median_spread_pct":0.0885,"median_iv_mid":0.2846,"median_iv_relative_range":0.0631,"min_log_moneyness":-0.1054,"max_log_moneyness":0.0953,"unique_strikes":7,"retention_rate":1.0,"iv_completion_rate":1.0,"log_moneyness_coverage":0.2007,"reliability_score":0.976},{"expiration":"2026-07-19","option_type":"put","total_quotes":7,"retained_quotes":6,"excluded_quotes":1,"complete_mid_iv_quotes":6,"median_spread_pct":0.0881,"median_iv_mid":0.3824,"median_iv_relative_range":0.0526,"min_log_moneyness":-0.1054,"max_log_moneyness":0.0953,"unique_strikes":7,"retention_rate":0.8571,"iv_completion_rate":0.8571,"log_moneyness_coverage":0.2007,"reliability_score":0.8771},{"expiration":"2026-06-21","option_type":"put","total_quotes":7,"retained_quotes":6,"excluded_quotes":1,"complete_mid_iv_quotes":6,"median_spread_pct":0.0881,"median_iv_mid":0.6653,"median_iv_relative_range":0.0782,"min_log_moneyness":-0.1054,"max_log_moneyness":0.0953,"unique_strikes":7,"retention_rate":0.8571,"iv_completion_rate":0.8571,"log_moneyness_coverage":0.2007,"reliability_score":0.8746},{"expiration":"2026-07-19","option_type":"call","total_quotes":7,"retained_quotes":6,"excluded_quotes":1,"complete_mid_iv_quotes":6,"median_spread_pct":0.0922,"median_iv_mid":0.3841,"median_iv_relative_range":0.0771,"min_log_moneyness":-0.1054,"max_log_moneyness":0.0953,"unique_strikes":7,"retention_rate":0.8571,"iv_completion_rate":0.8571,"log_moneyness_coverage":0.2007,"reliability_score":0.8738},{"expiration":"2026-06-21","option_type":"call","total_quotes":7,"retained_quotes":5,"excluded_quotes":2,"complete_mid_iv_quotes":5,"median_spread_pct":0.0744,"median_iv_mid":0.498,"median_iv_relative_range":0.0399,"min_log_moneyness":-0.1054,"max_log_moneyness":0.0953,"unique_strikes":7,"retention_rate":0.7143,"iv_completion_rate":0.7143,"log_moneyness_coverage":0.2007,"reliability_score":0.7811}],"scenario_summary":[{"scenario_name":"no_hedge_0bps","hedge_frequency":"no hedge","transaction_cost_bps":0.0,"hedge_mode":"none","path_count":3000,"mean_error":-0.026672,"std_error":4.452516,"p05_error":-3.029991,"p50_error":-3.029991,"p95_error":9.352529,"mean_abs_error":3.51849,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":0.0,"worst_5_percent_outcome":-3.029991,"risk_cost_score":3.51849},{"scenario_name":"weekly_0bps","hedge_frequency":"weekly","transaction_cost_bps":0.0,"hedge_mode":"fixed","path_count":3000,"mean_error":0.015363,"std_error":0.962638,"p05_error":-1.473565,"p50_error":-0.027516,"p95_error":1.615828,"mean_abs_error":0.735287,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":6.999,"worst_5_percent_outcome":-1.473565,"risk_cost_score":0.735287},{"scenario_name":"every_2_days_0bps","hedge_frequency":"every 2 days","transaction_cost_bps":0.0,"hedge_mode":"fixed","path_count":3000,"mean_error":0.006878,"std_error":0.652532,"p05_error":-1.021149,"p50_error":-0.012421,"p95_error":1.075493,"mean_abs_error":0.48857,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":15.957333,"worst_5_percent_outcome":-1.021149,"risk_cost_score":0.48857},{"scenario_name":"daily_0bps","hedge_frequency":"daily","transaction_cost_bps":0.0,"hedge_mode":"fixed","path_count":3000,"mean_error":0.007584,"std_error":0.458418,"p05_error":-0.732707,"p50_error":-0.001441,"p95_error":0.764149,"mean_abs_error":0.345017,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":30.807,"worst_5_percent_outcome":-0.732707,"risk_cost_score":0.345017},{"scenario_name":"event_triggered_0bps","hedge_frequency":"event triggered","transaction_cost_bps":0.0,"hedge_mode":"event","path_count":3000,"mean_error":0.015862,"std_error":0.56165,"p05_error":-0.90198,"p50_error":0.007493,"p95_error":0.950397,"mean_abs_error":0.439098,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":9.210667,"worst_5_percent_outcome":-0.90198,"risk_cost_score":0.439098},{"scenario_name":"no_hedge_1bps","hedge_frequency":"no hedge","transaction_cost_bps":1.0,"hedge_mode":"none","path_count":3000,"mean_error":-0.026672,"std_error":4.452516,"p05_error":-3.029991,"p50_error":-3.029991,"p95_error":9.352529,"mean_abs_error":3.51849,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":0.0,"worst_5_percent_outcome":-3.029991,"risk_cost_score":3.51849},{"scenario_name":"weekly_1bps","hedge_frequency":"weekly","transaction_cost_bps":1.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.00211,"std_error":0.961517,"p05_error":-1.492681,"p50_error":-0.046482,"p95_error":1.600235,"mean_abs_error":0.735117,"average_transaction_cost":0.017444,"max_transaction_cost":0.031868,"average_rebalance_count":6.999,"worst_5_percent_outcome":-1.492681,"risk_cost_score":0.752561},{"scenario_name":"every_2_days_1bps","hedge_frequency":"every 2 days","transaction_cost_bps":1.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.015498,"std_error":0.651309,"p05_error":-1.046007,"p50_error":-0.033679,"p95_error":1.046626,"mean_abs_error":0.488596,"average_transaction_cost":0.022339,"max_transaction_cost":0.041406,"average_rebalance_count":15.957333,"worst_5_percent_outcome":-1.046007,"risk_cost_score":0.510935},{"scenario_name":"daily_1bps","hedge_frequency":"daily","transaction_cost_bps":1.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.020054,"std_error":0.457201,"p05_error":-0.762526,"p50_error":-0.025975,"p95_error":0.73229,"mean_abs_error":0.345,"average_transaction_cost":0.027593,"max_transaction_cost":0.049011,"average_rebalance_count":30.807,"worst_5_percent_outcome":-0.762526,"risk_cost_score":0.372593},{"scenario_name":"event_triggered_1bps","hedge_frequency":"event triggered","transaction_cost_bps":1.0,"hedge_mode":"event","path_count":3000,"mean_error":-0.006046,"std_error":0.560398,"p05_error":-0.92382,"p50_error":-0.014289,"p95_error":0.922542,"mean_abs_error":0.438412,"average_transaction_cost":0.021873,"max_transaction_cost":0.043587,"average_rebalance_count":9.210667,"worst_5_percent_outcome":-0.92382,"risk_cost_score":0.460285},{"scenario_name":"no_hedge_5bps","hedge_frequency":"no hedge","transaction_cost_bps":5.0,"hedge_mode":"none","path_count":3000,"mean_error":-0.026672,"std_error":4.452516,"p05_error":-3.029991,"p50_error":-3.029991,"p95_error":9.352529,"mean_abs_error":3.51849,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":0.0,"worst_5_percent_outcome":-3.029991,"risk_cost_score":3.51849},{"scenario_name":"weekly_5bps","hedge_frequency":"weekly","transaction_cost_bps":5.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.072002,"std_error":0.957259,"p05_error":-1.561065,"p50_error":-0.10731,"p95_error":1.513608,"mean_abs_error":0.737696,"average_transaction_cost":0.087221,"max_transaction_cost":0.159338,"average_rebalance_count":6.999,"worst_5_percent_outcome":-1.561065,"risk_cost_score":0.824917},{"scenario_name":"every_2_days_5bps","hedge_frequency":"every 2 days","transaction_cost_bps":5.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.105,"std_error":0.646965,"p05_error":-1.137892,"p50_error":-0.120822,"p95_error":0.945624,"mean_abs_error":0.495719,"average_transaction_cost":0.111694,"max_transaction_cost":0.207028,"average_rebalance_count":15.957333,"worst_5_percent_outcome":-1.137892,"risk_cost_score":0.607413},{"scenario_name":"daily_5bps","hedge_frequency":"daily","transaction_cost_bps":5.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.130607,"std_error":0.453571,"p05_error":-0.87514,"p50_error":-0.126133,"p95_error":0.594884,"mean_abs_error":0.35919,"average_transaction_cost":0.137965,"max_transaction_cost":0.245053,"average_rebalance_count":30.807,"worst_5_percent_outcome":-0.87514,"risk_cost_score":0.497155},{"scenario_name":"event_triggered_5bps","hedge_frequency":"event triggered","transaction_cost_bps":5.0,"hedge_mode":"event","path_count":3000,"mean_error":-0.093677,"std_error":0.556195,"p05_error":-1.002744,"p50_error":-0.09777,"p95_error":0.818473,"mean_abs_error":0.443216,"average_transaction_cost":0.109365,"max_transaction_cost":0.217937,"average_rebalance_count":9.210667,"worst_5_percent_outcome":-1.002744,"risk_cost_score":0.552581},{"scenario_name":"no_hedge_10bps","hedge_frequency":"no hedge","transaction_cost_bps":10.0,"hedge_mode":"none","path_count":3000,"mean_error":-0.026672,"std_error":4.452516,"p05_error":-3.029991,"p50_error":-3.029991,"p95_error":9.352529,"mean_abs_error":3.51849,"average_transaction_cost":0.0,"max_transaction_cost":0.0,"average_rebalance_count":0.0,"worst_5_percent_outcome":-3.029991,"risk_cost_score":3.51849},{"scenario_name":"weekly_10bps","hedge_frequency":"weekly","transaction_cost_bps":10.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.159367,"std_error":0.952448,"p05_error":-1.633225,"p50_error":-0.194903,"p95_error":1.41,"mean_abs_error":0.747321,"average_transaction_cost":0.174443,"max_transaction_cost":0.318677,"average_rebalance_count":6.999,"worst_5_percent_outcome":-1.633225,"risk_cost_score":0.921764},{"scenario_name":"every_2_days_10bps","hedge_frequency":"every 2 days","transaction_cost_bps":10.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.216877,"std_error":0.642781,"p05_error":-1.255971,"p50_error":-0.229585,"p95_error":0.81718,"mean_abs_error":0.520284,"average_transaction_cost":0.223388,"max_transaction_cost":0.414055,"average_rebalance_count":15.957333,"worst_5_percent_outcome":-1.255971,"risk_cost_score":0.743672},{"scenario_name":"daily_10bps","hedge_frequency":"daily","transaction_cost_bps":10.0,"hedge_mode":"fixed","path_count":3000,"mean_error":-0.268799,"std_error":0.451863,"p05_error":-1.028552,"p50_error":-0.254862,"p95_error":0.443394,"mean_abs_error":0.409653,"average_transaction_cost":0.27593,"max_transaction_cost":0.490106,"average_rebalance_count":30.807,"worst_5_percent_outcome":-1.028552,"risk_cost_score":0.685583},{"scenario_name":"event_triggered_10bps","hedge_frequency":"event triggered","transaction_cost_bps":10.0,"hedge_mode":"event","path_count":3000,"mean_error":-0.203217,"std_error":0.552789,"p05_error":-1.114722,"p50_error":-0.19777,"p95_error":0.689412,"mean_abs_error":0.466375,"average_transaction_cost":0.21873,"max_transaction_cost":0.435875,"average_rebalance_count":9.210667,"worst_5_percent_outcome":-1.114722,"risk_cost_score":0.685105}],"hedging_error_bins":[-3.03,-2.3768,-1.7237,-1.0705,-0.4174,0.2358,0.8889,1.5421,2.1952,2.8483,3.5015,4.1546,4.8078,5.4609,6.1141,6.7672,7.4204,8.0735,8.7267,9.3798,10.033,10.6861,11.3393,11.9924,12.6456,13.2987,13.9519,14.605,15.2582,15.9113,16.5645],"scenario_histograms":{"daily_0bps":[0,1,37,441,1706,699,103,13,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"daily_10bps":[0,4,129,901,1648,285,32,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"daily_1bps":[0,1,44,478,1724,647,97,9,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"daily_5bps":[0,2,71,643,1741,484,52,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"event_triggered_0bps":[0,7,77,545,1361,829,164,15,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"event_triggered_10bps":[0,12,155,871,1339,552,64,6,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"event_triggered_1bps":[0,8,80,591,1352,803,152,12,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"event_triggered_5bps":[0,8,116,697,1378,686,104,10,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"every_2_days_0bps":[0,13,116,580,1310,761,156,48,11,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"every_2_days_10bps":[1,27,220,832,1307,486,82,36,7,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"every_2_days_1bps":[0,13,127,596,1323,736,141,48,11,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"every_2_days_5bps":[0,19,168,692,1335,615,118,40,10,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"no_hedge_0bps":[1631,92,96,88,91,92,74,111,79,67,70,56,69,47,44,51,30,32,30,23,24,16,15,10,8,9,9,10,7,4],"no_hedge_10bps":[1631,92,96,88,91,92,74,111,79,67,70,56,69,47,44,51,30,32,30,23,24,16,15,10,8,9,9,10,7,4],"no_hedge_1bps":[1631,92,96,88,91,92,74,111,79,67,70,56,69,47,44,51,30,32,30,23,24,16,15,10,8,9,9,10,7,4],"no_hedge_5bps":[1631,92,96,88,91,92,74,111,79,67,70,56,69,47,44,51,30,32,30,23,24,16,15,10,8,9,9,10,7,4],"weekly_0bps":[5,81,266,606,905,662,304,114,32,13,6,5,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"weekly_10bps":[13,116,338,738,873,548,253,82,16,12,9,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"weekly_1bps":[7,84,269,617,903,656,297,111,31,14,6,4,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],"weekly_5bps":[9,97,302,661,908,601,277,96,26,12,7,3,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0]},"sample_paths":[{"time_years":0.0,"path_0000":100.0,"path_0001":100.0,"path_0002":100.0,"path_0003":100.0,"path_0004":100.0,"path_0005":100.0,"path_0006":100.0,"path_0007":100.0,"path_0008":100.0,"path_0009":100.0,"path_0010":100.0,"path_0011":100.0,"path_0012":100.0,"path_0013":100.0,"path_0014":100.0},{"time_years":0.0027,"path_0000":100.4073,"path_0001":98.6566,"path_0002":100.9945,"path_0003":101.2459,"path_0004":97.4878,"path_0005":98.3188,"path_0006":100.1753,"path_0007":99.595,"path_0008":99.9859,"path_0009":98.8981,"path_0010":101.165,"path_0011":101.0306,"path_0012":100.0943,"path_0013":101.4935,"path_0014":100.6213},{"time_years":0.0055,"path_0000":99.8233,"path_0001":97.8087,"path_0002":101.5775,"path_0003":101.588,"path_0004":95.7202,"path_0005":99.7812,"path_0006":100.0598,"path_0007":98.1659,"path_0008":101.5609,"path_0009":99.7187,"path_0010":99.5131,"path_0011":103.415,"path_0012":100.9686,"path_0013":101.4879,"path_0014":102.7445},{"time_years":0.0082,"path_0000":100.1624,"path_0001":98.9686,"path_0002":101.9493,"path_0003":104.6154,"path_0004":97.535,"path_0005":99.3884,"path_0006":99.6522,"path_0007":98.7786,"path_0008":100.4615,"path_0009":101.2597,"path_0010":99.9928,"path_0011":103.7706,"path_0012":101.888,"path_0013":103.8092,"path_0014":102.9826},{"time_years":0.011,"path_0000":100.4657,"path_0001":98.9073,"path_0002":103.1163,"path_0003":105.4573,"path_0004":93.8063,"path_0005":100.1077,"path_0006":98.3604,"path_0007":96.9662,"path_0008":100.222,"path_0009":101.8135,"path_0010":97.8773,"path_0011":104.7397,"path_0012":102.9186,"path_0013":103.8812,"path_0014":101.8284},{"time_years":0.0137,"path_0000":100.913,"path_0001":100.5278,"path_0002":104.7776,"path_0003":104.8453,"path_0004":94.0521,"path_0005":97.7038,"path_0006":98.4957,"path_0007":95.9718,"path_0008":99.9859,"path_0009":99.6013,"path_0010":98.4048,"path_0011":102.4489,"path_0012":103.1265,"path_0013":102.2359,"path_0014":100.7109},{"time_years":0.0164,"path_0000":101.1539,"path_0001":101.7252,"path_0002":102.7871,"path_0003":104.463,"path_0004":95.0853,"path_0005":97.7954,"path_0006":100.4125,"path_0007":94.021,"path_0008":97.8074,"path_0009":100.6171,"path_0010":99.5334,"path_0011":102.1983,"path_0012":103.6762,"path_0013":103.2455,"path_0014":99.6522},{"time_years":0.0192,"path_0000":100.7528,"path_0001":101.8134,"path_0002":101.1403,"path_0003":102.5918,"path_0004":95.3198,"path_0005":96.8384,"path_0006":98.5304,"path_0007":95.2233,"path_0008":97.01,"path_0009":102.15,"path_0010":99.5784,"path_0011":102.6012,"path_0012":103.3979,"path_0013":99.7289,"path_0014":98.189},{"time_years":0.0219,"path_0000":100.5215,"path_0001":103.2569,"path_0002":104.1402,"path_0003":102.8413,"path_0004":95.3191,"path_0005":97.1707,"path_0006":97.6937,"path_0007":96.1886,"path_0008":97.5792,"path_0009":101.5976,"path_0010":100.7683,"path_0011":102.6347,"path_0012":102.1022,"path_0013":100.1966,"path_0014":98.5016},{"time_years":0.0246,"path_0000":98.8053,"path_0001":105.1587,"path_0002":103.675,"path_0003":102.7528,"path_0004":95.6808,"path_0005":95.5362,"path_0006":98.2233,"path_0007":95.6696,"path_0008":97.9625,"path_0009":100.8402,"path_0010":98.7236,"path_0011":102.0706,"path_0012":102.9697,"path_0013":100.7223,"path_0014":98.5493},{"time_years":0.0274,"path_0000":99.6389,"path_0001":107.3626,"path_0002":102.78,"path_0003":102.0303,"path_0004":95.4273,"path_0005":95.9084,"path_0006":98.3558,"path_0007":96.4364,"path_0008":96.5388,"path_0009":101.3731,"path_0010":97.7774,"path_0011":101.8874,"path_0012":105.3045,"path_0013":98.9046,"path_0014":98.1974},{"time_years":0.0301,"path_0000":97.5086,"path_0001":108.6301,"path_0002":102.7101,"path_0003":101.2407,"path_0004":95.1222,"path_0005":97.2256,"path_0006":99.3089,"path_0007":96.2828,"path_0008":95.1185,"path_0009":99.9738,"path_0010":98.7531,"path_0011":100.2065,"path_0012":105.1502,"path_0013":102.4429,"path_0014":98.7973},{"time_years":0.0329,"path_0000":97.4743,"path_0001":108.5869,"path_0002":102.963,"path_0003":100.4643,"path_0004":94.5984,"path_0005":96.7825,"path_0006":98.8976,"path_0007":95.8997,"path_0008":92.378,"path_0009":100.1095,"path_0010":98.0818,"path_0011":97.7968,"path_0012":104.678,"path_0013":101.9417,"path_0014":100.4671},{"time_years":0.0356,"path_0000":96.9447,"path_0001":109.9815,"path_0002":102.39,"path_0003":100.9398,"path_0004":94.4507,"path_0005":96.8464,"path_0006":99.0258,"path_0007":95.3497,"path_0008":90.9112,"path_0009":101.1258,"path_0010":100.1557,"path_0011":99.9505,"path_0012":103.9313,"path_0013":100.9766,"path_0014":99.7491},{"time_years":0.0383,"path_0000":96.8127,"path_0001":109.6908,"path_0002":101.9417,"path_0003":100.7899,"path_0004":93.9581,"path_0005":95.4262,"path_0006":100.1574,"path_0007":96.0034,"path_0008":93.1778,"path_0009":101.6238,"path_0010":99.6188,"path_0011":99.1426,"path_0012":104.0039,"path_0013":101.7176,"path_0014":99.4382},{"time_years":0.0411,"path_0000":95.188,"path_0001":108.8959,"path_0002":100.9721,"path_0003":100.7791,"path_0004":94.0937,"path_0005":94.1058,"path_0006":101.6181,"path_0007":95.8107,"path_0008":95.0347,"path_0009":101.9528,"path_0010":99.7167,"path_0011":98.5156,"path_0012":104.8521,"path_0013":101.7703,"path_0014":100.569},{"time_years":0.0438,"path_0000":93.9443,"path_0001":108.837,"path_0002":99.2172,"path_0003":99.8483,"path_0004":93.801,"path_0005":93.5952,"path_0006":102.597,"path_0007":94.8979,"path_0008":92.0204,"path_0009":99.737,"path_0010":99.7013,"path_0011":97.77,"path_0012":103.1776,"path_0013":104.4194,"path_0014":101.6732},{"time_years":0.0465,"path_0000":92.2083,"path_0001":108.8202,"path_0002":101.5949,"path_0003":102.9892,"path_0004":91.8429,"path_0005":92.7439,"path_0006":101.906,"path_0007":97.7467,"path_0008":91.9455,"path_0009":101.157,"path_0010":100.1008,"path_0011":96.2558,"path_0012":100.7057,"path_0013":103.5935,"path_0014":104.8101},{"time_years":0.0493,"path_0000":93.0371,"path_0001":110.0204,"path_0002":102.64,"path_0003":98.7274,"path_0004":91.7677,"path_0005":92.056,"path_0006":101.4115,"path_0007":97.3926,"path_0008":93.136,"path_0009":101.4334,"path_0010":99.4463,"path_0011":94.4322,"path_0012":102.7537,"path_0013":102.7281,"path_0014":104.6393},{"time_years":0.052,"path_0000":93.0739,"path_0001":110.8771,"path_0002":102.6698,"path_0003":98.5,"path_0004":91.8077,"path_0005":91.7183,"path_0006":103.4959,"path_0007":97.7452,"path_0008":92.5525,"path_0009":99.0703,"path_0010":99.1979,"path_0011":93.7297,"path_0012":101.9398,"path_0013":104.0108,"path_0014":104.7567},{"time_years":0.0548,"path_0000":92.3597,"path_0001":110.6094,"path_0002":101.5138,"path_0003":98.6879,"path_0004":88.9642,"path_0005":91.4725,"path_0006":103.3255,"path_0007":96.28,"path_0008":92.0982,"path_0009":100.5403,"path_0010":100.7648,"path_0011":93.0856,"path_0012":102.6484,"path_0013":101.9998,"path_0014":104.3599},{"time_years":0.0575,"path_0000":91.2862,"path_0001":108.8124,"path_0002":101.9644,"path_0003":98.8938,"path_0004":86.4194,"path_0005":89.9349,"path_0006":103.6791,"path_0007":96.1966,"path_0008":91.6237,"path_0009":101.348,"path_0010":98.8883,"path_0011":92.3712,"path_0012":103.3545,"path_0013":101.1451,"path_0014":104.7957},{"time_years":0.0602,"path_0000":89.6128,"path_0001":109.9662,"path_0002":102.6948,"path_0003":97.3381,"path_0004":87.5609,"path_0005":89.1239,"path_0006":104.2139,"path_0007":96.9903,"path_0008":91.3379,"path_0009":102.5695,"path_0010":98.7098,"path_0011":92.7887,"path_0012":102.9926,"path_0013":98.711,"path_0014":104.6347},{"time_years":0.063,"path_0000":89.6198,"path_0001":107.2667,"path_0002":102.0256,"path_0003":96.4995,"path_0004":87.5407,"path_0005":91.9581,"path_0006":102.892,"path_0007":97.515,"path_0008":91.6093,"path_0009":103.3316,"path_0010":98.4426,"path_0011":94.5623,"path_0012":103.9282,"path_0013":99.6284,"path_0014":102.7248},{"time_years":0.0657,"path_0000":90.3695,"path_0001":107.6998,"path_0002":102.8147,"path_0003":96.6069,"path_0004":87.7836,"path_0005":91.61,"path_0006":104.3597,"path_0007":98.2993,"path_0008":91.8239,"path_0009":103.158,"path_0010":96.1996,"path_0011":92.1462,"path_0012":103.4369,"path_0013":101.3036,"path_0014":101.79},{"time_years":0.0684,"path_0000":90.131,"path_0001":107.858,"path_0002":102.4925,"path_0003":96.2317,"path_0004":86.8389,"path_0005":90.3168,"path_0006":105.8797,"path_0007":96.1713,"path_0008":91.8086,"path_0009":103.0796,"path_0010":96.1481,"path_0011":92.9585,"path_0012":102.9445,"path_0013":102.1807,"path_0014":104.4772},{"time_years":0.0712,"path_0000":91.0502,"path_0001":105.2958,"path_0002":102.1798,"path_0003":94.876,"path_0004":90.1606,"path_0005":89.1457,"path_0006":103.8344,"path_0007":92.7558,"path_0008":90.5797,"path_0009":103.2535,"path_0010":97.533,"path_0011":91.6734,"path_0012":104.5425,"path_0013":102.1037,"path_0014":103.824},{"time_years":0.0739,"path_0000":90.3276,"path_0001":106.4381,"path_0002":103.1702,"path_0003":94.2222,"path_0004":91.959,"path_0005":87.8752,"path_0006":102.8459,"path_0007":94.691,"path_0008":89.053,"path_0009":103.7313,"path_0010":99.5624,"path_0011":88.6158,"path_0012":104.0899,"path_0013":103.3853,"path_0014":103.4661},{"time_years":0.0767,"path_0000":89.3941,"path_0001":104.9731,"path_0002":102.7938,"path_0003":95.4229,"path_0004":92.1727,"path_0005":88.5168,"path_0006":103.8638,"path_0007":93.9743,"path_0008":87.5802,"path_0009":102.9454,"path_0010":100.6458,"path_0011":89.3244,"path_0012":104.2058,"path_0013":104.6848,"path_0014":103.6715},{"time_years":0.0794,"path_0000":89.1107,"path_0001":103.4541,"path_0002":104.2605,"path_0003":95.1041,"path_0004":92.4763,"path_0005":87.7437,"path_0006":102.9222,"path_0007":94.5952,"path_0008":86.148,"path_0009":101.3984,"path_0010":102.6599,"path_0011":90.3021,"path_0012":104.7838,"path_0013":103.2345,"path_0014":103.9793},{"time_years":0.0821,"path_0000":89.7246,"path_0001":102.9784,"path_0002":101.9704,"path_0003":95.0246,"path_0004":91.0617,"path_0005":89.045,"path_0006":105.4077,"path_0007":95.3951,"path_0008":85.4359,"path_0009":101.436,"path_0010":103.0584,"path_0011":91.5997,"path_0012":104.5341,"path_0013":103.7953,"path_0014":101.7283}]};

const COLORS = {
  bg: "#F6F4EE",
  panel: "#FFFFFF",
  ink: "#20201D",
  muted: "#86807A",
  rule: "#E3DED2",
  navy: "#2D4356",
  rust: "#BC6C3A",
  sage: "#6F8F6F",
  danger: "#A8503F",
  amber: "#D9A24B",
};

const SERIF = "Georgia, 'Iowan Old Style', 'Times New Roman', serif";
const MONO = "'SF Mono', 'IBM Plex Mono', Menlo, Consolas, monospace";
const SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";

const FREQ_ORDER = ["no hedge", "weekly", "every 2 days", "daily", "event triggered"];
const FREQ_ORDER_HEDGED = FREQ_ORDER.filter((f) => f !== "no hedge");
const FREQ_LABELS = {
  "no hedge": "No Hedge",
  "weekly": "Weekly",
  "every 2 days": "Every 2 Days",
  "daily": "Daily",
  "event triggered": "Event Triggered",
};
const COST_LEVELS = [0, 1, 5, 10];

function fmt(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(digits);
}

function pct(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return (Number(value) * 100).toFixed(digits) + "%";
}

function Eyebrow({ children }) {
  return (
    <div
      style={{
        fontFamily: MONO,
        fontSize: "11px",
        letterSpacing: "0.14em",
        textTransform: "uppercase",
        color: COLORS.muted,
        marginBottom: "10px",
      }}
    >
      {children}
    </div>
  );
}

function Panel({ title, children, style }) {
  return (
    <div
      style={{
        background: COLORS.panel,
        border: `1px solid ${COLORS.rule}`,
        borderRadius: "2px",
        padding: "20px 22px",
        ...style,
      }}
    >
      {title && <Eyebrow>{title}</Eyebrow>}
      {children}
    </div>
  );
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div
      style={{
        background: COLORS.panel,
        border: `1px solid ${COLORS.rule}`,
        borderRadius: "2px",
        padding: "16px 18px",
        flex: "1 1 180px",
        minWidth: "160px",
      }}
    >
      <div
        style={{
          fontFamily: MONO,
          fontSize: "10px",
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          color: COLORS.muted,
          marginBottom: "8px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: SERIF,
          fontSize: "28px",
          color: accent || COLORS.ink,
          lineHeight: 1.1,
        }}
      >
        {value}
      </div>
      {sub && (
        <div style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "6px" }}>
          {sub}
        </div>
      )}
    </div>
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontFamily: SERIF,
        fontSize: "15px",
        background: "none",
        border: "none",
        borderBottom: active ? `2px solid ${COLORS.rust}` : "2px solid transparent",
        color: active ? COLORS.ink : COLORS.muted,
        padding: "10px 4px",
        marginRight: "28px",
        cursor: "pointer",
        transition: "color 0.15s ease",
      }}
    >
      {children}
    </button>
  );
}

function ChoiceButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontFamily: MONO,
        fontSize: "12px",
        letterSpacing: "0.04em",
        padding: "7px 14px",
        marginRight: "8px",
        marginBottom: "8px",
        border: `1px solid ${active ? COLORS.navy : COLORS.rule}`,
        background: active ? COLORS.navy : "transparent",
        color: active ? "#FFFFFF" : COLORS.ink,
        borderRadius: "2px",
        cursor: "pointer",
        transition: "all 0.12s ease",
      }}
    >
      {children}
    </button>
  );
}

export default function FrictionsLabDashboard() {
  const [tab, setTab] = useState("overview");
  const [expiration, setExpiration] = useState(null);
  const [optionType, setOptionType] = useState("call");
  const [frequency, setFrequency] = useState("daily");
  const [costBps, setCostBps] = useState(5);

  const dq = useMemo(() => {
    const map = {};
    DATA.data_quality.forEach((row) => (map[row.metric] = row.value));
    return map;
  }, []);

  const expirations = useMemo(
    () => Array.from(new Set(DATA.iv_quotes.map((d) => d.expiration))).sort(),
    []
  );

  const activeExpiration = expiration || expirations[0];

  const meanReliability = useMemo(() => {
    const vals = DATA.surface_diagnostics.map((d) => d.reliability_score);
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  }, []);

  const medianIvRelRange = useMemo(() => {
    const vals = DATA.iv_quotes
      .filter((d) => !d.is_excluded && d.IV_relative_range != null)
      .map((d) => d.IV_relative_range)
      .sort((a, b) => a - b);
    return vals[Math.floor(vals.length / 2)];
  }, []);

  const dailyFiveBps = useMemo(
    () => DATA.scenario_summary.find((s) => s.scenario_name === "daily_5bps"),
    []
  );

  const smileData = useMemo(() => {
    return DATA.iv_quotes
      .filter((d) => d.expiration === activeExpiration && d.option_type === optionType)
      .sort((a, b) => a.log_moneyness - b.log_moneyness);
  }, [activeExpiration, optionType]);

  const selectedScenario = useMemo(() => {
    const name = `${frequency === "no hedge" ? "no_hedge" : frequency === "every 2 days" ? "every_2_days" : frequency === "event triggered" ? "event_triggered" : frequency}_${costBps}bps`;
    return DATA.scenario_summary.find((s) => s.scenario_name === name);
  }, [frequency, costBps]);

  const histogramData = useMemo(() => {
    if (!selectedScenario) return [];
    const counts = DATA.scenario_histograms[selectedScenario.scenario_name] || [];
    const bins = DATA.hedging_error_bins;
    return counts.map((count, i) => ({
      center: (bins[i] + bins[i + 1]) / 2,
      count,
    }));
  }, [selectedScenario]);

  const frontierData = useMemo(() => {
    const byFreq = {};
    FREQ_ORDER.forEach((f) => (byFreq[f] = []));
    DATA.scenario_summary.forEach((s) => {
      if (byFreq[s.hedge_frequency]) {
        byFreq[s.hedge_frequency].push({
          cost: s.transaction_cost_bps,
          avgCost: s.average_transaction_cost,
          std: s.std_error,
        });
      }
    });
    Object.values(byFreq).forEach((arr) => arr.sort((a, b) => a.cost - b.cost));
    return byFreq;
  }, []);

  const heatmapMax = useMemo(
    () => Math.max(...DATA.scenario_summary.map((s) => s.mean_abs_error)),
    []
  );

  const pathSeries = useMemo(() => {
    return DATA.sample_paths.map((row) => {
      const out = { day: Math.round(row.time_years * 365.25) };
      Object.keys(row).forEach((k) => {
        if (k.startsWith("path_")) out[k] = row[k];
      });
      return out;
    });
  }, []);

  const pathKeys = useMemo(
    () => Object.keys(DATA.sample_paths[0]).filter((k) => k.startsWith("path_")),
    []
  );

  return (
    <div
      style={{
        background: COLORS.bg,
        color: COLORS.ink,
        fontFamily: SANS,
        minHeight: "100%",
        padding: "28px 32px 48px",
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: "18px" }}>
        <div style={{ fontFamily: MONO, fontSize: "11px", letterSpacing: "0.18em", color: COLORS.rust, textTransform: "uppercase", marginBottom: "6px" }}>
          SPY Option Chain &middot; Snapshot 2026-06-14
        </div>
        <h1 style={{ fontFamily: SERIF, fontSize: "32px", margin: 0, fontWeight: 400 }}>
          Option Market Frictions &amp; Hedging Error Lab
        </h1>
        <p style={{ fontFamily: SANS, fontSize: "14px", color: COLORS.muted, maxWidth: "720px", marginTop: "8px", lineHeight: 1.5 }}>
          Quote-quality, implied-volatility uncertainty, Greek sensitivity, short-expiry risk,
          and discrete delta-hedging error measured from bid, mid, and ask prices.
        </p>
      </div>

      {/* Ticker strip */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0",
          border: `1px solid ${COLORS.rule}`,
          background: COLORS.panel,
          marginBottom: "24px",
          fontFamily: MONO,
          fontSize: "12px",
        }}
      >
        {[
          ["Retained Contracts", `${dq.retained_contracts}/${dq.total_contracts}`],
          ["Median Spread %", pct(dq.median_spread_pct_retained)],
          ["Median IV Rel. Range", pct(medianIvRelRange)],
          ["Mean Surface Reliability", fmt(meanReliability, 2)],
          ["Daily 5bps Mean Error", dailyFiveBps ? fmt(dailyFiveBps.mean_error) : "—"],
        ].map(([label, value], i) => (
          <div
            key={label}
            style={{
              padding: "12px 20px",
              borderRight: i < 4 ? `1px solid ${COLORS.rule}` : "none",
              flex: "1 1 auto",
            }}
          >
            <div style={{ color: COLORS.muted, textTransform: "uppercase", letterSpacing: "0.08em", fontSize: "10px", marginBottom: "4px" }}>
              {label}
            </div>
            <div style={{ fontSize: "16px", color: COLORS.navy }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: `1px solid ${COLORS.rule}`, marginBottom: "24px" }}>
        <TabButton active={tab === "overview"} onClick={() => setTab("overview")}>Overview</TabButton>
        <TabButton active={tab === "quality"} onClick={() => setTab("quality")}>Quote Quality</TabButton>
        <TabButton active={tab === "vol"} onClick={() => setTab("vol")}>Volatility &amp; Greeks</TabButton>
        <TabButton active={tab === "hedging"} onClick={() => setTab("hedging")}>Hedging Scenarios</TabButton>
      </div>

      {tab === "overview" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
            <StatCard label="Unique Expiries" value={dq.unique_expiries} sub="2026-06-21 / 07-19 / 09-18" />
            <StatCard label="Excluded Share" value={pct(dq.excluded_share)} sub="zero bid, crossed market, wide spread, low liquidity" accent={COLORS.danger} />
            <StatCard label="Median DTE (retained)" value={fmt(dq.median_days_to_expiry_retained, 1)} sub="days to expiry" />
            <StatCard label="Mean Spread %" value={pct(dq.mean_spread_pct_retained)} sub="bid-ask spread / mid price" accent={COLORS.rust} />
          </div>

          <Panel title="Volatility Surface Reliability — by expiry and option type">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={DATA.surface_diagnostics.map((d) => ({
                label: `${d.expiration.slice(5)} ${d.option_type}`,
                reliability_score: d.reliability_score,
              }))} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} vertical={false} />
                <XAxis dataKey="label" tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                <YAxis domain={[0, 1]} tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                <Tooltip contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }} />
                <Bar dataKey="reliability_score" fill={COLORS.navy} radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "8px" }}>
              The reliability score blends retention rate, IV completion rate, spread tightness,
              and IV uncertainty into a single 0–1 diagnostic per expiry slice. Near-dated
              contracts score lower because their quotes carry wider relative spreads.
            </p>
          </Panel>

          <Panel title="Simulated Stock Price Paths — geometric Brownian motion (30 days, 15 of 2,000 paths shown)">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={pathSeries} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} vertical={false} />
                <XAxis dataKey="day" tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} label={{ value: "Day", position: "insideBottom", offset: -4, fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                <YAxis domain={["auto", "auto"]} tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                <Tooltip contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }} />
                {pathKeys.map((k, i) => (
                  <Line
                    key={k}
                    type="monotone"
                    dataKey={k}
                    stroke={i % 3 === 0 ? COLORS.navy : i % 3 === 1 ? COLORS.rust : COLORS.sage}
                    strokeWidth={1}
                    dot={false}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
            <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "8px" }}>
              These paths drive the discrete delta-hedging simulation in the Hedging Scenarios tab.
              Each path is rebalanced on its own schedule, and the spread of terminal values is
              what produces the hedging error distribution.
            </p>
          </Panel>
        </div>
      )}

      {tab === "quality" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <Panel title="Exclusion Reasons — 42 raw contracts">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={DATA.exclusion_reasons}
                layout="vertical"
                margin={{ top: 8, right: 24, left: 24, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} horizontal={false} />
                <XAxis type="number" tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                <YAxis
                  type="category"
                  dataKey="exclusion_reason"
                  width={120}
                  tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                />
                <Tooltip contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }} />
                <Bar dataKey="contract_count" radius={[0, 2, 2, 0]}>
                  {DATA.exclusion_reasons.map((entry, i) => (
                    <Cell key={i} fill={entry.exclusion_reason === "retained" ? COLORS.sage : COLORS.danger} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Panel>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
            <Panel title="What gets filtered, and why">
              <p style={{ fontFamily: SANS, fontSize: "13px", lineHeight: 1.6, margin: 0 }}>
                Of 42 raw SPY contracts across three expiries, <strong>37 (88%)</strong> pass the
                quote-quality filters. The five exclusions are split evenly across <em>zero
                bid</em>, <em>crossed market</em>, <em>missing bid/ask</em>, <em>wide spread</em>
                {" "}(spread &gt; 40% of mid price), and <em>low liquidity</em> (zero volume and
                open interest). Every downstream calculation — implied volatility, Greeks,
                surfaces — uses only the retained 37.
              </p>
            </Panel>
            <Panel title="Spread by Moneyness &amp; Expiry">
              <p style={{ fontFamily: SANS, fontSize: "13px", lineHeight: 1.6, margin: 0 }}>
                Retained quotes carry a median bid-ask spread of{" "}
                <strong>{pct(dq.median_spread_pct_retained)}</strong> of the mid price (mean{" "}
                {pct(dq.mean_spread_pct_retained)}). Spreads widen for deep
                out-of-the-money strikes and for the nearest expiry, which is the core
                quote-friction signal this project tracks into the implied-volatility step.
              </p>
            </Panel>
          </div>
        </div>
      )}

      {tab === "vol" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <Panel title="Bid / Mid / Ask Implied Volatility Smile">
            <div style={{ marginBottom: "14px" }}>
              {expirations.map((exp) => (
                <ChoiceButton key={exp} active={activeExpiration === exp} onClick={() => setExpiration(exp)}>
                  {exp}
                </ChoiceButton>
              ))}
              <span style={{ display: "inline-block", width: "12px" }} />
              {["call", "put"].map((ot) => (
                <ChoiceButton key={ot} active={optionType === ot} onClick={() => setOptionType(ot)}>
                  {ot.toUpperCase()}
                </ChoiceButton>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={smileData} margin={{ top: 8, right: 16, left: 0, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} vertical={false} />
                <XAxis
                  dataKey="log_moneyness"
                  type="number"
                  domain={["auto", "auto"]}
                  tickFormatter={(v) => v.toFixed(2)}
                  tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                  label={{ value: "log-moneyness ln(K/S)", position: "insideBottom", offset: -14, fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                />
                <YAxis tickFormatter={(v) => pct(v, 0)} tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                <Tooltip
                  contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }}
                  formatter={(v) => pct(v, 2)}
                  labelFormatter={(v) => `ln(K/S) = ${Number(v).toFixed(3)}`}
                />
                <Legend verticalAlign="top" height={28} wrapperStyle={{ fontFamily: MONO, fontSize: 11 }} />
                <Line type="monotone" dataKey="IV_bid" name="IV Bid" stroke={COLORS.rust} strokeWidth={1.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="IV_mid" name="IV Mid" stroke={COLORS.navy} strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="IV_ask" name="IV Ask" stroke={COLORS.sage} strokeWidth={1.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
            <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "8px" }}>
              Each contract's implied volatility is solved three times — once from the bid
              price, once from the mid price, and once from the ask price. The gap between the
              bid and ask curves is the implied-volatility uncertainty created by the
              bid-ask spread.
            </p>
          </Panel>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
            <Panel title="IV Relative Range by Moneyness Bucket">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={DATA.iv_by_moneyness} margin={{ top: 8, right: 8, left: 0, bottom: 32 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} vertical={false} />
                  <XAxis
                    dataKey="moneyness_bucket"
                    tick={{ fontFamily: MONO, fontSize: 9, fill: COLORS.muted }}
                    angle={-35}
                    textAnchor="end"
                    height={70}
                    interval={0}
                  />
                  <YAxis tickFormatter={(v) => pct(v, 0)} tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                  <Tooltip contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }} formatter={(v) => pct(v, 2)} />
                  <Bar dataKey="median_iv_relative_range" fill={COLORS.rust} radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="Gamma &amp; |Theta| by Days-to-Expiry Bucket">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={DATA.short_expiry_summary.map((d) => ({
                  label: `${d.dte_bucket.replace(/_/g, " ")} (${d.option_type})`,
                  median_gamma: d.median_gamma,
                  median_abs_theta_per_day: d.median_abs_theta / 365,
                }))} margin={{ top: 8, right: 8, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} vertical={false} />
                  <XAxis dataKey="label" tick={{ fontFamily: MONO, fontSize: 9, fill: COLORS.muted }} angle={-35} textAnchor="end" height={90} interval={0} />
                  <YAxis
                    yAxisId="gamma"
                    tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.navy }}
                    label={{ value: "Gamma", angle: -90, position: "insideLeft", fontFamily: MONO, fontSize: 11, fill: COLORS.navy }}
                  />
                  <YAxis
                    yAxisId="theta"
                    orientation="right"
                    tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.rust }}
                    label={{ value: "|Theta| / day ($)", angle: 90, position: "insideRight", fontFamily: MONO, fontSize: 11, fill: COLORS.rust }}
                  />
                  <Tooltip contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }} />
                  <Legend verticalAlign="top" height={28} wrapperStyle={{ fontFamily: MONO, fontSize: 11 }} />
                  <Bar yAxisId="gamma" dataKey="median_gamma" name="Median Gamma" fill={COLORS.navy} radius={[2, 2, 0, 0]} />
                  <Bar yAxisId="theta" dataKey="median_abs_theta_per_day" name="Median |Theta| / day ($)" fill={COLORS.rust} radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "8px" }}>
                Gamma (left axis) and |Theta| per day (right axis, annualized theta &divide; 365)
                are shown on separate scales since Theta decay is orders of magnitude larger
                in dollar terms.
              </p>
            </Panel>
          </div>

          <Panel title="Greek Uncertainty Ranges — Delta and Gamma vs. Log-Moneyness">
            <ResponsiveContainer width="100%" height={280}>
              <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} />
                <XAxis
                  dataKey="log_moneyness"
                  type="number"
                  domain={["auto", "auto"]}
                  tickFormatter={(v) => v.toFixed(2)}
                  tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                  label={{ value: "log-moneyness ln(K/S)", position: "insideBottom", offset: -4, fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                />
                <YAxis
                  dataKey="Delta_range"
                  type="number"
                  tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                  label={{ value: "Delta range (bid-ask)", angle: -90, position: "insideLeft", fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                />
                <ZAxis dataKey="Gamma_range" range={[20, 220]} name="Gamma range" />
                <Tooltip
                  contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }}
                  formatter={(v, name) => (name === "Gamma range" ? fmt(v, 4) : fmt(v, 4))}
                />
                <Scatter
                  name="Contracts"
                  data={DATA.greeks.filter((d) => !d.is_excluded)}
                  fill={COLORS.rust}
                  fillOpacity={0.55}
                />
              </ScatterChart>
            </ResponsiveContainer>
            <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "8px" }}>
              Each point is one retained contract. The vertical position is the Delta
              uncertainty range implied by bid/ask IV; bubble size encodes the Gamma
              uncertainty range. Both widen for short-dated, away-from-the-money contracts.
            </p>
          </Panel>
        </div>
      )}

      {tab === "hedging" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <Panel title="Scenario Controls">
            <div style={{ display: "flex", flexWrap: "wrap", gap: "24px" }}>
              <div>
                <div style={{ fontFamily: MONO, fontSize: "10px", letterSpacing: "0.1em", color: COLORS.muted, textTransform: "uppercase", marginBottom: "8px" }}>
                  Hedge Frequency
                </div>
                <div>
                  {FREQ_ORDER.map((f) => (
                    <ChoiceButton key={f} active={frequency === f} onClick={() => setFrequency(f)}>
                      {FREQ_LABELS[f]}
                    </ChoiceButton>
                  ))}
                </div>
              </div>
              <div>
                <div style={{ fontFamily: MONO, fontSize: "10px", letterSpacing: "0.1em", color: COLORS.muted, textTransform: "uppercase", marginBottom: "8px" }}>
                  Transaction Cost
                </div>
                <div>
                  {COST_LEVELS.map((c) => (
                    <ChoiceButton key={c} active={costBps === c} onClick={() => setCostBps(c)}>
                      {c} bps
                    </ChoiceButton>
                  ))}
                </div>
              </div>
            </div>
          </Panel>

          {selectedScenario && (
            <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
              <StatCard label="Mean Hedging Error" value={fmt(selectedScenario.mean_error)} accent={COLORS.navy} />
              <StatCard label="Std. Dev. of Error" value={fmt(selectedScenario.std_error)} accent={COLORS.rust} />
              <StatCard label="P05 / P95 Error" value={`${fmt(selectedScenario.p05_error, 2)} / ${fmt(selectedScenario.p95_error, 2)}`} />
              <StatCard label="Mean Abs. Error" value={fmt(selectedScenario.mean_abs_error)} />
              <StatCard label="Avg. Transaction Cost" value={fmt(selectedScenario.average_transaction_cost)} accent={COLORS.rust} />
              <StatCard label="Avg. Rebalances" value={fmt(selectedScenario.average_rebalance_count, 1)} />
            </div>
          )}

          <Panel title={`Hedging Error Distribution — ${FREQ_LABELS[frequency]}, ${costBps} bps (3,000 paths)`}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={histogramData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} vertical={false} />
                <XAxis
                  dataKey="center"
                  type="number"
                  domain={["auto", "auto"]}
                  tickFormatter={(v) => v.toFixed(1)}
                  tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                  label={{ value: "Hedging error ($)", position: "insideBottom", offset: -4, fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                />
                <YAxis tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }} />
                <Tooltip
                  contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }}
                  labelFormatter={(v) => `error ≈ ${Number(v).toFixed(2)}`}
                />
                <ReferenceLine x={0} stroke={COLORS.ink} strokeDasharray="3 3" />
                <Bar dataKey="count" fill={COLORS.navy} />
              </BarChart>
            </ResponsiveContainer>
            <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "8px" }}>
              Hedging error is the terminal value of the option-plus-hedge portfolio after 30
              days of discrete rebalancing. A tighter, more centered distribution means the
              hedge tracked the option's value more closely.
            </p>
          </Panel>

          <Panel title="Hedge-Frequency Cost-Risk Frontier">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart margin={{ top: 8, right: 16, left: 0, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.rule} vertical={false} />
                <XAxis
                  dataKey="avgCost"
                  type="number"
                  tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                  label={{ value: "Average transaction cost ($)", position: "insideBottom", offset: -14, fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                />
                <YAxis
                  type="number"
                  tick={{ fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                  label={{ value: "Std. dev. of hedging error", angle: -90, position: "insideLeft", fontFamily: MONO, fontSize: 11, fill: COLORS.muted }}
                />
                <Tooltip contentStyle={{ fontFamily: MONO, fontSize: 12, border: `1px solid ${COLORS.rule}` }} formatter={(v) => fmt(v, 3)} />
                <Legend verticalAlign="top" height={28} wrapperStyle={{ fontFamily: MONO, fontSize: 11 }} />
                {FREQ_ORDER_HEDGED.map((f, i) => (
                  <Line
                    key={f}
                    data={frontierData[f]}
                    dataKey="std"
                    name={FREQ_LABELS[f]}
                    stroke={f === frequency ? COLORS.rust : [COLORS.navy, COLORS.sage, COLORS.amber, COLORS.danger][i]}
                    strokeWidth={f === frequency ? 3 : 1.5}
                    dot={{ r: f === frequency ? 4 : 2 }}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
            <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "8px" }}>
              Moving right along a line means accepting higher trading costs; moving down
              means lower outcome variance. No hedge sits far above this chart
              (std. dev. &asymp; {fmt(DATA.scenario_summary.find((s) => s.scenario_name === "no_hedge_0bps").std_error, 2)})
              and is excluded from the axis to keep the hedged frequencies readable. The
              highlighted line is the current selection.
            </p>
          </Panel>

          <Panel title="Mean Absolute Hedging Error — Frequency &times; Transaction Cost">
            <div style={{ overflowX: "auto" }}>
              <table style={{ borderCollapse: "collapse", fontFamily: MONO, fontSize: "12px", minWidth: "480px" }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left", padding: "6px 10px", color: COLORS.muted, fontWeight: "normal" }}></th>
                    {COST_LEVELS.map((c) => (
                      <th key={c} style={{ textAlign: "center", padding: "6px 10px", color: COLORS.muted, fontWeight: "normal" }}>
                        {c} bps
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {FREQ_ORDER.map((f) => (
                    <tr key={f}>
                      <td style={{ padding: "6px 10px", color: COLORS.ink, whiteSpace: "nowrap" }}>{FREQ_LABELS[f]}</td>
                      {COST_LEVELS.map((c) => {
                        const name = `${f === "no hedge" ? "no_hedge" : f === "every 2 days" ? "every_2_days" : f === "event triggered" ? "event_triggered" : f}_${c}bps`;
                        const row = DATA.scenario_summary.find((s) => s.scenario_name === name);
                        const value = row ? row.mean_abs_error : null;
                        const intensity = value != null ? Math.min(value / heatmapMax, 1) : 0;
                        const isSelected = f === frequency && c === costBps;
                        return (
                          <td
                            key={c}
                            onClick={() => { setFrequency(f); setCostBps(c); }}
                            style={{
                              padding: "10px 14px",
                              textAlign: "center",
                              cursor: "pointer",
                              color: intensity > 0.6 ? "#FFFFFF" : COLORS.ink,
                              background: `rgba(188,108,58,${0.12 + intensity * 0.78})`,
                              border: isSelected ? `2px solid ${COLORS.navy}` : `1px solid ${COLORS.rule}`,
                            }}
                          >
                            {value != null ? fmt(value, 3) : "—"}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p style={{ fontFamily: SANS, fontSize: "12px", color: COLORS.muted, marginTop: "10px" }}>
              Darker cells mean larger average absolute hedging error. Click a cell to load
              that scenario above. Daily rebalancing has the lowest error at every cost
              level, but its advantage narrows as transaction costs rise.
            </p>
          </Panel>
        </div>
      )}
    </div>
  );
}
