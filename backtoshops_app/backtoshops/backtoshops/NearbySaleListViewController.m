//
//  NearbySaleListViewController.m
//  backtoshops
//
//  Created by Ding Nicholas on 3/16/12.
//  Copyright (c) 2012 Nicholas Ding. All rights reserved.
//

#import "NearbySaleListViewController.h"
#import "AFHTTPRequestOperation.h"
#import "GDataXMLNode.h"
#import "Sale.h"
#import "SVProgressHUD.h"

@implementation NearbySaleListViewController

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:@"SaleListViewController" bundle:nil];
    if (self) {
        self.items = [NSArray array];
        
        locationManager = [[CLLocationManager alloc] init];
        locationManager.delegate = self;
        locationManager.desiredAccuracy = kCLLocationAccuracyHundredMeters;
    }
    return self;
}

- (void)viewDidLoad
{
    [super viewDidLoad];
    
    self.navigationController.navigationBar.tintColor = [UIColor colorWithRed:251.0/255.0 green:195.0/255.0 blue:38.0/255.0 alpha:1];
    
    [locationManager startUpdatingLocation];
    
    [SVProgressHUD showInView:self.view status:nil networkIndicator:YES];
    
    self.previousButton.hidden = YES;
    self.nextButton.hidden = YES;
}

- (void)loadSales:(CLLocationCoordinate2D)coordinate radius:(NSInteger)radius
{
    if (isLoading) return;
    
    isLoading = YES;
    
    // Load Sales
    NSString *params = [NSString stringWithFormat:@"lat=%f&lng=%f&radius=%d", coordinate.latitude, coordinate.longitude, radius];
    NSURLRequest *request = [NSURLRequest requestWithURL:[NSURL URLWithString:[@"http://sales.backtoshops.com/webservice/1.0/vicinity/sales?" stringByAppendingString:params]]];
    
    AFHTTPRequestOperation *saleListOperation = [[[AFHTTPRequestOperation alloc] initWithRequest:request] autorelease];
    [saleListOperation setCompletionBlockWithSuccess:^(AFHTTPRequestOperation *operation, id responseObject) {
        NSError *error;
        GDataXMLDocument *doc = [[GDataXMLDocument alloc] initWithData:responseObject options:0 error:&error];
        NSMutableArray *saleList = [NSMutableArray array];
        for (GDataXMLElement *el in [doc.rootElement elementsForName:@"sale"]) {
            Sale *saleObj = [Sale saleFromXML:el];
            [saleList addObject:saleObj];
        }
        
        self.items = [saleList copy];
        
        if ([self.items count] > 0) {
            [self loadWebViewWithSale:[self.items objectAtIndex:0]];
        }
        
        [doc release];
        
        isLoading = NO;
        [SVProgressHUD dismiss];
    } failure:^(AFHTTPRequestOperation *operation, NSError *error) {
        NSLog(@"Load nearby sales %@", error);
        isLoading = NO;
        [SVProgressHUD dismiss];
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    [queue addOperation:saleListOperation];
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

#pragma mark - CLLocationManagerDelegate

- (void)locationManager:(CLLocationManager *)manager didUpdateToLocation:(CLLocation *)newLocation fromLocation:(CLLocation *)oldLocation
{
    if (!isLocationLoaded) {
        isLocationLoaded = YES;
        [self loadSales:newLocation.coordinate radius:20000];
        [manager stopUpdatingLocation];
    }
}

@end
