//
//  AppDelegate.m
//  backtoshops
//
//  Created by Ding Nicholas on 1/31/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import "AppDelegate.h"

#import "MainTabController.h"

@implementation AppDelegate

@synthesize window = _window;

- (void)dealloc
{
    [_window release];
    [super dealloc];
}

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
    self.window = [[[UIWindow alloc] initWithFrame:[[UIScreen mainScreen] bounds]] autorelease];

    // Override point for customization after application launch.
    application.statusBarStyle = UIStatusBarStyleBlackOpaque;
    
    // Override default appearance
    [[UINavigationBar appearance] setBackgroundImage:[UIImage imageNamed:@"navbar"] forBarMetrics:UIBarMetricsDefault];
    [[UINavigationBar appearance] setTitleTextAttributes:
         [NSDictionary dictionaryWithObjectsAndKeys:
              [UIColor colorWithRed:0x4f/255.0 green:0 blue:0 alpha:1.0],
              UITextAttributeTextColor,
              [NSValue valueWithUIOffset:UIOffsetMake(0, 0)], 
              UITextAttributeTextShadowOffset,
              nil]];
    [[UIBarButtonItem appearance] setTitleTextAttributes:
         [NSDictionary dictionaryWithObjectsAndKeys:
              [UIColor colorWithRed:0x4f/255.0 green:0 blue:0 alpha:1.0], 
              UITextAttributeTextColor, 
              [NSValue valueWithUIOffset:UIOffsetMake(0, 0)], 
              UITextAttributeTextShadowOffset, 
              [UIFont systemFontOfSize:12],
              UITextAttributeFont,
              nil] 
         forState:UIControlStateNormal];
    
    MainTabController *controller = [[MainTabController alloc] initWithNibName:@"MainTabController" bundle:nil];
    controller.view.frame = CGRectMake(0, 20, 320, 460);
    
    [self.window addSubview:controller.view];
    [self.window makeKeyAndVisible];
    
//    [controller presentLoginViewController:NO];
    
    return YES;
}

- (void)applicationWillResignActive:(UIApplication *)application
{
    /*
     Sent when the application is about to move from active to inactive state. This can occur for certain types of temporary interruptions (such as an incoming phone call or SMS message) or when the user quits the application and it begins the transition to the background state.
     Use this method to pause ongoing tasks, disable timers, and throttle down OpenGL ES frame rates. Games should use this method to pause the game.
     */
}

- (void)applicationDidEnterBackground:(UIApplication *)application
{
    /*
     Use this method to release shared resources, save user data, invalidate timers, and store enough application state information to restore your application to its current state in case it is terminated later. 
     If your application supports background execution, this method is called instead of applicationWillTerminate: when the user quits.
     */
}

- (void)applicationWillEnterForeground:(UIApplication *)application
{
    /*
     Called as part of the transition from the background to the inactive state; here you can undo many of the changes made on entering the background.
     */
}

- (void)applicationDidBecomeActive:(UIApplication *)application
{
    /*
     Restart any tasks that were paused (or not yet started) while the application was inactive. If the application was previously in the background, optionally refresh the user interface.
     */
}

- (void)applicationWillTerminate:(UIApplication *)application
{
    /*
     Called when the application is about to terminate.
     Save data if appropriate.
     See also applicationDidEnterBackground:.
     */
}

@end
