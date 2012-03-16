//
//  NearbySaleListViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 3/16/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import "SaleListViewController.h"
#import <CoreLocation/CoreLocation.h>

@interface NearbySaleListViewController : SaleListViewController <CLLocationManagerDelegate> {
    CLLocationManager *locationManager;
    BOOL               isLocationLoaded;
}

- (void)loadSales:(CLLocationCoordinate2D)coordinate radius:(NSInteger)radius;

@end
