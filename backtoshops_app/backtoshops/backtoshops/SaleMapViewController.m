//
//  SaleMapViewController.m
//  backtoshops
//
//  Created by Ding Nicholas on 3/5/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import "SaleMapViewController.h"
#import "ShopAnnotation.h"
#import "Shop.h"
#import "SaleShopInfoViewController.h"
#import "UIImageView+AFNetworking.h"

@implementation SaleMapViewController

@synthesize mapView;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        // Custom initialization
    }
    return self;
}

- (id)initWithSale:(Sale *)_sale
{
    self = [self initWithNibName:@"SaleMapViewController" bundle:nil];
    if (self) {
        sale = [_sale retain];
    }
    return self;
}

- (void)dealloc
{
    [sale release];
    [mapView release];
    [super dealloc];
}

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = NSLocalizedString(@"Plan", nil);
    
    [self.mapView.userLocation addObserver:self forKeyPath:@"location" options:(NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld) context:NULL];
    
    // Sale Info
    UIImageView *thumbnail = (UIImageView *)[self.view viewWithTag:1];
    [thumbnail setImageWithURL:[NSURL URLWithString:[@"http://sales.backtoshops.com" stringByAppendingString:sale.imageURL]]];
    UILabel *name = (UILabel *)[self.view viewWithTag:2];
    name.text = sale.name;
    UILabel *discount = (UILabel *)[self.view viewWithTag:3];
    discount.text = [NSString stringWithFormat:@"%@€00", sale.discountPrice];
    UILabel *price = (UILabel *)[self.view viewWithTag:4];
    price.text = [NSString stringWithFormat:@"au lieu de %@€00", sale.price];
    UILabel *ratio = (UILabel *)[self.view viewWithTag:5];
    ratio.text = [NSString stringWithFormat:@"-%@%%", sale.discountRatio];
    
    // Place pins
    for (Shop *shop in sale.shops) {
        ShopAnnotation *anno = [[ShopAnnotation alloc] init];
        anno.title = shop.name;
        anno.shopID = shop.identifier;
        [anno setCoordinate:shop.coordinate];
        [self.mapView addAnnotation:anno];
        [anno release];
    }
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
            span.latitudeDelta  = 1; // Change these values to change the zoom
            span.longitudeDelta = 1; 
            region.span = span;
            
            [self.mapView setRegion:region animated:YES];
        }
    }
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
    SaleShopInfoViewController *controller = [[SaleShopInfoViewController alloc] initWithSale:sale shopID:annotation.shopID];
    [self.navigationController pushViewController:controller animated:YES];
    [controller release];
}

@end
