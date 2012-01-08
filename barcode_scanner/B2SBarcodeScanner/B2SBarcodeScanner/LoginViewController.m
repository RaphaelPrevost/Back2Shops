//
//  ViewController.m
//  B2SBarcodeScanner
//
//  Created by Ding Nicholas on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import "LoginViewController.h"
#import "AFHTTPClient.h"
#import "AFJSONRequestOperation.h"
#import "SVProgressHUD.h"

@implementation LoginViewController

@synthesize usernameField;
@synthesize passwordField;

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Release any cached data, images, etc that aren't in use.
}

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = @"Login";
}

- (void)viewDidUnload
{
    [self setUsernameField:nil];
    [self setPasswordField:nil];
    [super viewDidUnload];
    // Release any retained subviews of the main view.
    // e.g. self.myOutlet = nil;
}

- (void)viewWillAppear:(BOOL)animated
{
    [super viewWillAppear:animated];
}

- (void)viewDidAppear:(BOOL)animated
{
    [super viewDidAppear:animated];
}

- (void)viewWillDisappear:(BOOL)animated
{
	[super viewWillDisappear:animated];
}

- (void)viewDidDisappear:(BOOL)animated
{
	[super viewDidDisappear:animated];
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    // Return YES for supported orientations
    return (interfaceOrientation != UIInterfaceOrientationPortraitUpsideDown);
}

- (void)dealloc {
    [usernameField release];
    [passwordField release];
    [super dealloc];
}

- (IBAction)login:(id)sender
{
    [SVProgressHUD showInView:self.view];
    
    NSURL *url = [NSURL URLWithString:API_HOST];
 
    AFHTTPClient *client = [AFHTTPClient clientWithBaseURL:url];
    [client setAuthorizationHeaderWithUsername:self.usernameField.text password:self.passwordField.text];
    NSURLRequest *request = [client requestWithMethod:@"GET" path:@"/webservice/1.0/private/auth" parameters:nil];
    
    AFJSONRequestOperation *operation = [AFJSONRequestOperation JSONRequestOperationWithRequest:request success:^(NSURLRequest *request, NSHTTPURLResponse *response, id JSON) {
        if ([[JSON valueForKey:@"success"] boolValue]) {
            [SVProgressHUD dismissWithSuccess:@"Login succeed."];
            
            NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
            [defaults setBool:YES forKey:@"logged"];
            [defaults synchronize];
            
            [self dismissModalViewControllerAnimated:YES];
        } else {
            [SVProgressHUD dismissWithError:@"Please check your username and password."];
        }
    } failure:^(NSURLRequest *request, NSHTTPURLResponse *response, NSError *error, id JSON) {
        [SVProgressHUD dismissWithError:@"Login failed"];
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    [queue addOperation:operation];
}

@end
