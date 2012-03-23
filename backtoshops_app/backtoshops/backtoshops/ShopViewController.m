//
//  ShopViewController.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/3/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "ShopViewController.h"
#import "ShopAnnotation.h"
#import "AFHTTPRequestOperation.h"
#import "GDataXMLNode.h"
#import "ShopInfoViewController.h"

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

    self.title = NSLocalizedString(@"Plan", @"Title of ShopViewController");
    self.navigationController.navigationBar.tintColor = [UIColor colorWithRed:251.0/255.0 green:195.0/255.0 blue:38.0/255.0 alpha:1];
    
    [self.mapView.userLocation addObserver:self forKeyPath:@"location" options:(NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld) context:NULL];
}

- (void)loadAllShops
{
    MKCoordinateRegion region;
    region.center = self.mapView.userLocation.coordinate;
    
    MKCoordinateSpan span; 
    span.latitudeDelta  = 4; // Change these values to change the zoom
    span.longitudeDelta = 4; 
    region.span = span;
    
    [self.mapView setRegion:region animated:YES];
    
    // Load shop list from webservice
    NSURLRequest *request = [NSURLRequest requestWithURL:[NSURL URLWithString:@"http://sales.backtoshops.com/webservice/1.0/pub/shops/list"]];
    AFHTTPRequestOperation *operation = [[[AFHTTPRequestOperation alloc] initWithRequest:request] autorelease];
    [operation setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
        NSError *error;
        GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
        for (GDataXMLElement *shop in [doc.rootElement elementsForName:@"shop"]) {
            ShopAnnotation *shopAnno = [[ShopAnnotation alloc] init];
            shopAnno.title = [[[shop elementsForName:@"name"] lastObject] stringValue];
            shopAnno.shopID = [[shop attributeForName:@"id"] stringValue];
            
            GDataXMLElement *location = [[shop elementsForName:@"location"] lastObject];
            CLLocationDegrees lat = [[[location attributeForName:@"lat"] stringValue] doubleValue];
            CLLocationDegrees lng = [[[location attributeForName:@"long"] stringValue] doubleValue];
            [shopAnno setCoordinate:CLLocationCoordinate2DMake(lat, lng)];
            [self.mapView addAnnotation:shopAnno];
            [shopAnno release];
        }
        
        [doc release];
    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
        
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    [queue addOperation:operation];
}

- (void)loadNearbyShops:(CLLocationCoordinate2D)coordinate radius:(NSInteger)radius
{
    // Load shop list from webservice
    NSString *params = [NSString stringWithFormat:@"lat=%f&lng=%f&radius=%d", coordinate.latitude, coordinate.longitude, radius];
    NSURLRequest *request = [NSURLRequest requestWithURL:[NSURL URLWithString:[@"http://sales.backtoshops.com/webservice/1.0/vicinity/shops?" stringByAppendingString:params]]];
    AFHTTPRequestOperation *operation = [[[AFHTTPRequestOperation alloc] initWithRequest:request] autorelease];
    [operation setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
        NSError *error;
        GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
        for (GDataXMLElement *shop in [doc.rootElement elementsForName:@"shop"]) {
            ShopAnnotation *shopAnno = [[ShopAnnotation alloc] init];
            shopAnno.title = [[[shop elementsForName:@"name"] lastObject] stringValue];
            shopAnno.shopID = [[shop attributeForName:@"id"] stringValue];
            
            GDataXMLElement *location = [[shop elementsForName:@"location"] lastObject];
            CLLocationDegrees lat = [[[location attributeForName:@"lat"] stringValue] doubleValue];
            CLLocationDegrees lng = [[[location attributeForName:@"long"] stringValue] doubleValue];
            [shopAnno setCoordinate:CLLocationCoordinate2DMake(lat, lng)];
            [self.mapView addAnnotation:shopAnno];
            [shopAnno release];
        }
        
        if ([[doc.rootElement elementsForName:@"shop"] count] == 0) {
            [self loadAllShops];
        }
        
        [doc release];
    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
        
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    [queue addOperation:operation];    
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
            [self loadNearbyShops:self.mapView.userLocation.location.coordinate radius:20000]; // radius = 20 km
        }
    }
}

- (void)dealloc
{
    [self.mapView.userLocation removeObserver:self forKeyPath:@"location"];
    
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
    ShopAnnotation *annotation = (ShopAnnotation *)view.annotation;
    ShopInfoViewController *controller = [[ShopInfoViewController alloc] initWithShopID:annotation.shopID];
    [self.navigationController pushViewController:controller animated:YES];
    [controller release];
}

@end
