//
//  SearchViewController.h
//  backtoshops
//
//  Created by Ding Nicholas on 5/2/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import <UIKit/UIKit.h>
#import <MapKit/MapKit.h>

@interface SearchViewController : UIViewController <UITextFieldDelegate, MKMapViewDelegate> {
    NSMutableArray *saleList;
    BOOL isLocationLoaded;
}

@property (retain, nonatomic) IBOutlet MKMapView *mapView;

@end
