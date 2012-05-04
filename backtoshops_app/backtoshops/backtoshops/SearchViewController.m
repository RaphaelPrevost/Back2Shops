//
//  SearchViewController.m
//  backtoshops
//
//  Created by Ding Nicholas on 5/2/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import "SearchViewController.h"
#import "LocalCache.h"
#import "Sale.h"
#import "Shop.h"
#import "SaleAnnotation.h"
#import "SaleListViewController.h"

@interface SearchViewController (Private)

- (void)searchSalesByName:(NSString *)name;

@end

@implementation SearchViewController

@synthesize mapView;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        saleList = [[NSMutableArray alloc] init];
    }
    return self;
}

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = NSLocalizedString(@"Trouver", @"Title of SearchViewController");
    self.navigationController.navigationBar.tintColor = [UIColor colorWithRed:251.0/255.0 green:195.0/255.0 blue:38.0/255.0 alpha:1];
    
    [self.mapView.userLocation addObserver:self forKeyPath:@"location" options:(NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld) context:NULL];
}

- (void)viewDidUnload
{
    [self setMapView:nil];
    [super viewDidUnload];
    // Release any retained subviews of the main view.
    // e.g. self.myOutlet = nil;
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)dealloc
{
    [mapView release];
    [saleList release];
    [super dealloc];
}

- (void)observeValueForKeyPath:(NSString *)keyPath  
                      ofObject:(id)object  
                        change:(NSDictionary *)change  
                       context:(void *)context
{
    if (!isLocationLoaded) {
        if ([self.mapView showsUserLocation]) {
            [self.mapView setCenterCoordinate:self.mapView.userLocation.location.coordinate animated:NO];
            isLocationLoaded = YES;
            MKCoordinateRegion region;
            region.center = self.mapView.userLocation.coordinate;
            
            MKCoordinateSpan span; 
            span.latitudeDelta  = 0.4; // Change these values to change the zoom
            span.longitudeDelta = 0.4; 
            region.span = span;
            
            [self.mapView setRegion:region animated:YES];
//            [self loadNearbyShops:self.mapView.userLocation.location.coordinate radius:20000]; // radius = 20 km
        }
    }
}

#pragma mark - UITextFieldDelegate

- (BOOL)textFieldShouldReturn:(UITextField *)textField
{
    [self searchSalesByName:textField.text];
    [textField resignFirstResponder];
    
    return YES;
}

#pragma mark - MKMapViewDelegate

- (MKAnnotationView *)mapView:(MKMapView *)mapView viewForAnnotation:(id<MKAnnotation>)annotation
{
    if ([annotation isKindOfClass:[MKUserLocation class]]) {
        return nil;
    }
    
    MKPinAnnotationView *aView = [[MKPinAnnotationView alloc] initWithAnnotation:annotation reuseIdentifier:@"FoundSale"];
    aView.animatesDrop = YES;
    aView.pinColor = MKPinAnnotationColorGreen;
    aView.canShowCallout = YES;
    aView.enabled = YES;
    aView.rightCalloutAccessoryView = [UIButton buttonWithType:UIButtonTypeDetailDisclosure];
    return aView;
}

- (void)mapView:(MKMapView *)mapView annotationView:(MKAnnotationView *)view calloutAccessoryControlTapped:(UIControl *)control
{   
    SaleListViewController *controller = [[SaleListViewController alloc] initWithItems:saleList];
    [self.navigationController pushViewController:controller animated:YES];
    [controller release];
}

#pragma mark - Private

- (void)searchSalesByName:(NSString *)name
{
    // Remove annotations
    [self.mapView removeAnnotations:self.mapView.annotations];
    
    // Search from cache
    NSDictionary *saleMap = [[LocalCache sharedLocalCache] cachedDictionaryWithKey:@"SaleMap"];
    if (!saleMap) return;
    
    [saleList removeAllObjects];
    
    for (NSString *key in saleMap.allKeys) {
        Sale *saleObj = [saleMap valueForKey:key];
        NSRange range = [saleObj.name rangeOfString:name];
        if (range.location != NSNotFound) {
            [saleList addObject:saleObj];
        }
    }
    
    for (Sale *saleObj in saleList) {
        if (!saleObj.shops) continue;
        
        Shop *shopObj = [saleObj.shops objectAtIndex:0];
        SaleAnnotation *annotation = [[SaleAnnotation alloc] init];
        annotation.title = saleObj.name;
        annotation.coordinate = shopObj.coordinate;
        [self.mapView addAnnotation:annotation];
        [annotation release];
    }
}

@end
