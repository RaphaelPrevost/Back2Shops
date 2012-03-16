//
//  ShopViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/3/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <UIKit/UIKit.h>
#import <MapKit/MapKit.h>

@interface ShopViewController : UIViewController <MKMapViewDelegate> {
    BOOL isLocationLoaded;
}

@property (retain, nonatomic) IBOutlet MKMapView *mapView;

- (void)loadAllShops;
- (void)loadNearbyShops:(CLLocationCoordinate2D)coordinate radius:(NSInteger)radius;

@end
