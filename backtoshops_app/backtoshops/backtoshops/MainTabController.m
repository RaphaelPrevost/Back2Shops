//
//  MainTabController.m
//  backtoshops
//
//  Created by Ding Nicholas on 2/2/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "MainTabController.h"
#import "HomeViewController.h"
#import "ShopViewController.h"
#import "LoginViewController.h"

@interface MainTabController (Private)

- (void)deselectTab;

@end

@implementation MainTabController

@synthesize viewControllers;
@synthesize currentController;
@synthesize contentView;
@synthesize tabbar;

- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        self.viewControllers = [[NSMutableArray alloc] init];
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
    // Do any additional setup after loading the view from its nib.

//    HomeViewController *c1 = [[[HomeViewController alloc] initWithNibName:@"HomeViewController" bundle:nil] autorelease];
//    [self.contentView addSubview:c1.view];
    
    UINavigationController *firstController = [[[UINavigationController alloc] init] autorelease];
    firstController.view.frame = CGRectMake(0, 0, 320, 415);
    [firstController pushViewController:[[[ShopViewController alloc] initWithNibName:@"ShopViewController" bundle:nil] autorelease] animated:NO];
    [self.viewControllers addObject:firstController];
    
    UINavigationController *secondController = [[[UINavigationController alloc] init] autorelease];
    secondController.view.frame = CGRectMake(0, 0, 320, 415);
//    [secondController pushViewController:[[[SaleInfoViewController alloc] initWithSaleID:@"1"] autorelease] animated:NO];
    [self.viewControllers addObject:secondController];
    
    [self click1st:nil];
    
//    for (int i = 0; i < 3; i++) {
//        UIViewController *c;
//        if (i == 0) {
//            c = [[ShopViewController alloc] initWithNibName:@"ShopViewController" bundle:nil];
//            c.title = @"Plan";
//        } else {
//            c = [[UIViewController alloc] init];
//            c.title = [NSString stringWithFormat:@"C - %d", i];
//        }
//        
//        UINavigationController *nav = [[UINavigationController alloc] init];
//        nav.view.frame = CGRectMake(0, 20, 320, 410);
//        [nav pushViewController:c animated:YES];
//        
//        [self.viewControllers addObject:nav];
//        
//        [c release];
//        [nav release];
//    }
//    
//    self.currentController = [self.viewControllers objectAtIndex:0];
}

- (void)viewDidUnload
{
    [super viewDidUnload];
    // Release any retained subviews of the main view.
    // e.g. self.myOutlet = nil;
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    // Return YES for supported orientations
    return (interfaceOrientation == UIInterfaceOrientationPortrait);
}

- (void)setCurrentController:(UIViewController *)_currentController
{
    if (self.currentController) {
        [self.currentController.view removeFromSuperview];
    }
    
    [self.contentView addSubview:_currentController.view];
    
    [currentController release];
    currentController = [_currentController retain];
}

- (void)presentLoginViewController:(BOOL)animated
{
    LoginViewController *controller = [[LoginViewController alloc] initWithNibName:@"LoginViewController" bundle:nil];
    [self presentModalViewController:controller animated:animated];
    [controller release];
}

- (IBAction)click1st:(id)sender
{
//    UIViewController *c = [[[UIViewController alloc] init] autorelease];
//    c.title = @"Hello 1st";
//    
//    UINavigationController *nav = [self.viewControllers objectAtIndex:0];
//    [nav pushViewController:c animated:YES];

    [self deselectTab];
    
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagFirst];
    imageView.image = [UIImage imageNamed:@"icons_01_on"];
    
    self.currentController = [self.viewControllers objectAtIndex:0];
}

- (IBAction)click2nd:(id)sender
{
//    UIViewController *c = [[[UIViewController alloc] init] autorelease];
//    c.title = @"Hello 2nd";
//    
//    UINavigationController *nav = [self.viewControllers objectAtIndex:1];
//    [nav pushViewController:c animated:YES];

    [self deselectTab];
    
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagSecond];
    imageView.image = [UIImage imageNamed:@"icons_02_on"];
    
    self.currentController = [self.viewControllers objectAtIndex:1];
}

- (IBAction)click3rd:(id)sender
{
//    UIViewController *c = [[[UIViewController alloc] init] autorelease];
//    c.title = @"Hello 3rd";
//    
//    UINavigationController *nav = [self.viewControllers objectAtIndex:2];
//    [nav pushViewController:c animated:YES];
    
    [self deselectTab];
    
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagThird];
    imageView.image = [UIImage imageNamed:@"icons_03_on"];

    self.currentController = [self.viewControllers objectAtIndex:2];
}

#pragma mark - Private

- (void)deselectTab
{
    UIImageView *imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagFirst];
    imageView.image = [UIImage imageNamed:@"icons_01_off"];

    imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagSecond];
    imageView.image = [UIImage imageNamed:@"icons_02_off"];
    
    imageView = (UIImageView *)[self.tabbar viewWithTag:ButtonImageTagThird];
    imageView.image = [UIImage imageNamed:@"icons_03_off"];
}

@end