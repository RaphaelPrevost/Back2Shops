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

#pragma mark - View lifecycle

- (void)viewDidLoad
{
    [super viewDidLoad];

    self.title = @"Login";
    
    NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
    if ([defaults valueForKey:@"Username"]) {
        self.usernameField.text = [defaults valueForKey:@"Username"];
    }
    
    [self.usernameField becomeFirstResponder];
}

- (void)viewDidUnload
{
    [self setUsernameField:nil];
    [self setPasswordField:nil];
    [super viewDidUnload];
}

- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)interfaceOrientation
{
    // Return YES for supported orientations
    return (interfaceOrientation != UIInterfaceOrientationPortraitUpsideDown);
}

- (void)dealloc
{
    [usernameField release];
    [passwordField release];
    [super dealloc];
}

- (IBAction)login:(id)sender
{
    [SVProgressHUD showInView:self.view status:@"Loading..." networkIndicator:YES posY:150];
    
    NSURL *url = [NSURL URLWithString:API_HOST];
 
    AFHTTPClient *client = [AFHTTPClient clientWithBaseURL:url];
    [client setAuthorizationHeaderWithUsername:self.usernameField.text password:self.passwordField.text];
    NSURLRequest *request = [client requestWithMethod:@"GET" path:@"/webservice/1.0/private/auth" parameters:nil];
    
    AFJSONRequestOperation *operation = [AFJSONRequestOperation JSONRequestOperationWithRequest:request success:^(NSURLRequest *request, NSHTTPURLResponse *response, id JSON) {
        if ([[JSON valueForKey:@"success"] boolValue]) {
            [SVProgressHUD dismissWithSuccess:@"Login succeed."];
            
            NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
            [defaults setBool:YES forKey:@"logged"];
            [defaults setValue:self.usernameField.text forKey:@"Username"];
            [defaults setValue:self.passwordField.text forKey:@"Password"];
            [defaults synchronize];
            
            [self dismissModalViewControllerAnimated:YES];
        } else {
            [SVProgressHUD dismissWithError:@"Please check your username and password."];
        }
    } failure:^(NSURLRequest *request, NSHTTPURLResponse *response, NSError *error, id JSON) {
        NSLog(@"%@", error);
        [SVProgressHUD dismissWithError:@"Login failed"];
    }];
    
    NSOperationQueue *queue = [[[NSOperationQueue alloc] init] autorelease];
    [queue addOperation:operation];
}

@end
