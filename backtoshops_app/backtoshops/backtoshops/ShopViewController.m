//
//  ShopViewController.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/3/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "ShopViewController.h"
#import "ShopAnnotation.h"

@implementation ShopViewController
@synthesize mapView;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        // Custom initialization
    }
    return self;
}

- (void)didReceiveMemoryWarning
{
    // Releases the view if it doesn't have a superview.
    [super didReceiveMemoryWarning];
    
    // Release any cached data, images, etc that aren't in use.
}

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = @"Plan";
    self.navigationController.navigationBar.tintColor = [UIColor colorWithRed:251.0/255.0 green:195.0/255.0 blue:38.0/255.0 alpha:1];
    
    [self.mapView.userLocation addObserver:self forKeyPath:@"location" options:(NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld) context:NULL];
    
    ShopAnnotation *shop1 = [[[ShopAnnotation alloc] init] autorelease];
    shop1.title = @"Beijing";
    shop1.subtitle = @"";
    [shop1 setCoordinate:CLLocationCoordinate2DMake(40.1447, 117.2720)];
    [self.mapView addAnnotation:shop1];
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
    // Return YES for supported orientations
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)observeValueForKeyPath:(NSString *)keyPath  
                      ofObject:(id)object  
                        change:(NSDictionary *)change  
                       context:(void *)context
{
    if ([self.mapView showsUserLocation]) {
        [self.mapView setCenterCoordinate:self.mapView.userLocation.location.coordinate animated:NO];
//        MKCoordinateRegion region;
//        region.center = self.mapView.userLocation.coordinate;  
//        
//        MKCoordinateSpan span; 
//        span.latitudeDelta  = 1; // Change these values to change the zoom
//        span.longitudeDelta = 1; 
//        region.span = span;
//        
//        [self.mapView setRegion:region animated:YES];
    }
}

- (void)dealloc
{
    [mapView release];
    [super dealloc];
}

#pragma mark - MKMapViewDelegate

- (MKAnnotationView *)mapView:(MKMapView *)mapView viewForAnnotation:(id<MKAnnotation>)annotation
{
    if ([annotation isKindOfClass:[MKUserLocation class]]) {
        return nil;
    }
    
    MKPinAnnotationView *aView = [[MKPinAnnotationView alloc] initWithAnnotation:annotation reuseIdentifier:@"location"];
    aView.pinColor = MKPinAnnotationColorGreen;
    aView.canShowCallout = YES;
    aView.enabled = YES;
    aView.rightCalloutAccessoryView = [UIButton buttonWithType:UIButtonTypeDetailDisclosure];
    return aView;
}

- (void)mapView:(MKMapView *)mapView annotationView:(MKAnnotationView *)view calloutAccessoryControlTapped:(UIControl *)control
{
    NSLog(@"Clicked %@", view.annotation);
}

@end
