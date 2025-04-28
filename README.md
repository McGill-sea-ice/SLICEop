# SLICEop
Operational forecast of the St. Lawrence river's freeze-up date near Montreal, QC, Canada

We use September total cloud cover, November snowfall and December 2 m – air temperature from the [ECMWF's seasonal forecast system](https://www.ecmwf.int/en/forecasts/documentation-and-support/long-range)
to perform a multiple linear regression that predicts the date on which the water temperature near Montreal drops to the freezing point and ice formation begins.​

The water temperature and actual date of freeze-up are observed at the [Longueuil water treatment plant](https://www.longueuil.quebec/fr/eau-potable) near Montreal.

The three predictor variables have been found to best predict the freeze-up date based on [extensive testing by Amélie Bouchat](https://github.com/McGill-sea-ice/SLICE).
They also tested the use of machine learning, which was found to perform worse on medium to seasonal time scales. 
