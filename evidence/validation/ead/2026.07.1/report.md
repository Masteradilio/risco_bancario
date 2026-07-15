# Independent EAD/CCF backtest — ead_amortized_and_revolving_ccf

- Model version: `synthetic-2026.07.1`
- Policy: `2026.07.1` (`ab4fafe14e704aca1e474ebbd6a12c5fcc731e1db933458f3f3dc937cea34700`)
- Evidence hash: `cc75b17cf9978bbbb68549be4a88cc86fdfe667afeb2756186517e46a295ac91`
- Decision: **rejected**
- Report hash: `8d402a738f436b8643c2ce3dce46cffcd9f70276f92bc2112297ef82b6e953a5`
- Excluded: `off_balance_without_realized_history`

| Component | Dimension | Value | N | Predicted EAD | Actual EAD | EAD MAE | EAD relative MAE | Predicted CCF | Actual CCF | CCF MAE | CCF RMSE | Pass |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| amortized | aggregate | all | 24 | 128765.4029166666666666666667 | 128765.4029166666666666666667 | 0.00 | 0E+20 | NA | NA | NA | NA | true |
| revolving | aggregate | all | 4 | 6280.72273429482365680995 | 4494.12 | 1813.93916350840356999140 | 0.4036249952178409944530631136 | 0.037665013100403767 | 0.044671705 | 0.039723048146353122 | 0.05489365851281653227103802173 | false |
| amortized | product | acquired_distressed | 8 | 41169.6875 | 41169.6875 | 0.00 | 0E+2 | NA | NA | NA | NA | false |
| amortized | product | mortgage | 8 | 302893.43 | 302893.43 | 0.00 | 0 | NA | NA | NA | NA | false |
| amortized | product | vehicle_finance | 8 | 42233.09125 | 42233.09125 | 0.00 | 0E+3 | NA | NA | NA | NA | false |
| revolving | product | credit_card | 2 | 12174.33189780322722680135 | 8618.70 | 3555.63189780322722680135 | 0.4125485163427462641467216634 | 0.032716356246756889 | 0E-8 | 0.032716356246756889 | 0.04073438695156003240027857188 | false |
| revolving | product | overdraft | 2 | 387.11357078642008681855 | 369.54 | 72.24642921357991318145 | 0.1955036781230175709840612654 | 0.042613669954050645 | 0.08934341 | 0.046729740045949355 | 0.06608583213915071564908621249 | false |
| revolving | utilization_band | low | 1 | 314.8671415728401736371 | 369.54 | 54.6728584271598263629 | 0.1479484181067268126938897007 | 0.08522733990810129 | 0.17868682 | 0.09345948009189871 | 0.09345948009189871000000000000 | false |
| revolving | utilization_band | medium | 3 | 8269.341265202151484534233333 | 5868.98 | 2400.361265202151484534233333 | 0.4089912157141703472382310611 | 0.02181090416450459266666666667 | 0E-8 | 0.02181090416450459266666666667 | 0.03325948767213574332187501664 | false |

## Decision reasons

- revolving sample below objective minimum
- revolving error exceeds objective limit

> Synthetic retrospective validation evidence; not institutional model approval.
