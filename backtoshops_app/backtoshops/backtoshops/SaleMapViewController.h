//
//  SaleMapViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 3/5/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import <UIKit/UIKit.h>
#import <MapKit/MapKit.h>
#import "Sale.h"

@interface SaleMapViewController : UIViewController <MKMapViewDelegate> {
    Sale *sale;
}

@property (retain, nonatomic) IBOutlet MKMapView *mapView;

- (id)initWithSale:(Sale *)sale;

@end
