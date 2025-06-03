import simpy
import numpy as np
np.random.seed(42)

def generate_customer(env, TOTAL_CUSTOMERS, INTERVAL):
    """
    A process function that creates customers at fixed intervals (INTERVAL) within the simulation environment.
    This function generates a new customer in the SimPy environment (env) every INTERVAL time units,
    and stops after producing a total of TOTAL_CUSTOMERS.
    Args:
        TOTAL_CUSTOMERS (int): The total number of customers to generate.
        INTERVAL (float): The time interval (in simulation time units) between successive customer creations.

    Yields:
        simpy.Event: A SimPy timeout event that pauses the process for INTERVAL time units.
            After INTERVAL has passed, a new customer is generated and the loop continues.
    """
    print('#########################New_Process_Start#####################################')
    for i in range(TOTAL_CUSTOMERS):
        customer_name = i
        customer_has_blueprint = np.random.randint(0, 2)
        env.process(recept_customer(env, customer_name, reception_desk, customer_has_blueprint))
        yield env.timeout(np.random.exponential(INTERVAL))

def recept_customer(env, customer_name, reception_desk, customer_has_blueprint):
    """
    A process function that handles a customer going through the reception desk and then moving to the next step in the SimPy environment.

    This function records the customer's arrival, makes them wait for the reception desk resource,
    checks if their wait time exceeds a specified limit (in which case they leave),
    and if they are served, it simulates service time and then directs the customer to create a blueprint
    if they do not have one, or to the printing process if they already have a blueprint.


    Args:
        customer_name (str): The customer's identifier
        reception_desk (simpy.Resource): The SimPy Resource object representing the reception desk.
        customer_has_blueprint (int): A flag indicating whether the customer has a blueprint (0 or 1).

    Yields:
        env (simpy.Environment): The SimPy simulation environment.
            Used to track current simulation time for arrival and wait calculations,
            and to create timeout events for service delays.
        customer_name (str): The customer's identifier (name or ID).
            Passed as a unique string for printing messages and subsequent process calls.
        reception_desk (simpy.Resource): The SimPy Resource object representing the reception desk.
            Configured with capacity=1, so customers queue and are served one at a time.
        customer_has_blueprint (int): A flag indicating whether the customer has a blueprint (0 or 1).
            If 0, the function calls the create_blueprint process;
            if 1, it proceeds directly to the printing_process.
    """
    customer_arrive_time = env.now
    print("# Enter Process 0 Time {:.2f} # Customer {} arrived at {:.2f}".format(env.now, customer_name, customer_arrive_time))

    with reception_desk.request() as req:
        yield req
        customer_wait_time = env.now - customer_arrive_time
        customer_wait_limit = 500
        if customer_wait_time > customer_wait_limit:
            print("# Fail Process 0 Time {:.2f} # Customer {} leave".format(env.now, customer_name))
        else:
            if customer_wait_time != 0:
                print('# Proceed Process 0 Time {:.2f} # Customer {}  wait. during {:.2f}'.format(env.now, customer_name, customer_wait_time))
            service_time = np.random.triangular(3, 6, 9)
            yield env.timeout(service_time)
            if customer_has_blueprint == 0:
                yield env.process(create_blueprint(env, customer_name, blueprint_station))
            else:
                printer_type = np.random.randint(0, 2)
                print('# finish Process 0 Time {:.2f} # Customer {}'.format(env.now, customer_name))
                yield env.process(printing_process(env, customer_name, printer_type))
                

def create_blueprint(env, customer_name, blueprint_station):
    """
    A process function that handles a customer’s blueprint creation.

    Args:
        customer_name (str): Identifier for the customer.
        blueprint_station (simpy.Resource): The SimPy Resource representing the blueprint creation station.

    Yields:
        simpy.Event:
            1) `yield req` waits for the blueprint_station request event until the station is available.
            2) `yield env.timeout(process_time)` pauses for the sampled creation time to complete the blueprint.
            3) After printing the completion message, `yield env.process(printing_process(...))` suspends
               this process while the printing process runs.
    """
    process_time = np.random.triangular(4, 10, 15)
    with blueprint_station.request() as req:
        yield req
        yield env.timeout(process_time)
        print('# finish Process 0 Time {:.2f} # Customer {} complete blueprint creation.'.format(env.now, customer_name))
    printer_type = np.random.randint(0, 2)
    yield env.process(printing_process(env, customer_name, printer_type))

def printing_process(env, customer_name, printer_type):
    """
    A function that, within the simulation environment, selects the first available printer 
    (either FDM or SLA based on the given printer_type), performs the printing job on that printer, 
    and then proceeds to the quality inspection (qc_team.inspect) process.

    Args:
        customer_name (str): Identifier for the customer.
        printer_type (int): Flag indicating the type of printer (0 for FDM, 1 for SLA).

    Yields:
        simpy.events.AnyOf: Waits for the first available printer resource among two requests.
        simpy.Event: The event returned by `env.process(selected_printer.print(...))`, which completes when printing is done.
        simpy.Event: The event returned by `env.process(qc_team.inspect(...))`, which completes when quality inspection is done.
        

    Process Steps:
        1. If printer_type is 0, request the two FDM printers (fdm_printer_1, fdm_printer_2); 
           otherwise, request the two SLA printers (sla_printer_1, sla_printer_2).
        2. Use simpy.events.AnyOf to choose whichever printer becomes available first, 
           and cancel the other request.
        3. Call `yield env.process(selected_printer.print(customer_name))` to execute the printing job 
           on the selected printer.
        4. After printing is complete, release the printer resource with 
           `selected_printer.resource.release(selected_req)`.
        5. Next, invoke the `qc_team.inspect` process to carry out the quality inspection.
        6. Once all tasks are done, print a message indicating that printing and inspection are complete.
    """
    if printer_type == 0:
        req1 = fdm_printer_1.resource.request()
        req2 = fdm_printer_2.resource.request()
        result = yield simpy.events.AnyOf(env, [req1, req2])

        if req1 in result:
            selected_printer = fdm_printer_1
            selected_req = req1
            req2.cancel()
        else:
            selected_printer = fdm_printer_2
            selected_req = req2
            req1.cancel()

    else:
        req1 = sla_printer_1.resource.request()
        req2 = sla_printer_2.resource.request()
        result = yield simpy.events.AnyOf(env, [req1, req2])

        if req1 in result:
            selected_printer = sla_printer_1
            selected_req = req1
            req2.cancel()
        else:
            selected_printer = sla_printer_2
            selected_req = req2
            req1.cancel()

    print("# enter Process 1 Time {:.2f} # Customer {} dispatched to {}"
          .format(env.now, customer_name, selected_printer.__class__.__name__))

    yield env.process(selected_printer.print(customer_name))

    selected_printer.resource.release(selected_req)
    
    yield env.process(qc_team.inspect(customer_name, printer_type))

#-----------------------------------------------------
class Printer:
    """
    An abstract class defining the basic functions common to printers used in the simulation environment.
    """
    def __init__(self, env):
        self.env=env

        
        
class FDMPrinter_1(Printer):   
    """    
    A class modeling the first FDM (Fused Deposition Modeling) printer.

    Attributes:
        resource (simpy.Resource): A SimPy Resource object representing FDMPrinter_1 (capacity=1).
    """
    def __init__(self, env):
        super().__init__(env)
        self.resource=simpy.Resource(env,capacity=1)
        
    def print(self, customer_name):
        """
        A process method that carries out a 3D printing job for a customer.

        1. Determines the required amount of plastic (needed_plastic) using a triangular distribution 
           (min=1g, mode=2g, max=3g).
        2. Determines the printing time (print_time_FDM1) using a triangular distribution 
           (min=8 minutes, mode=10 minutes, max=20 minutes).
        3. Prints a message including the current simulation time (env.now), customer name, and plastic usage.
        4. Calls the use_material.get_plastic process to obtain the required plastic amount.
        5. Waits for the specified print_time, then prints a completion message.

        Args:
            customer_name (str): The identifier for customer

        Yields:
            simpy.Event: Sequentially waits for use_material.get_plastic and env.timeout events, 
            then signals that printing is complete.
        """
        needed_plastic = np.random.triangular(1, 2, 3)
        print_time_FDM1=np.random.triangular(8,10,20)
        print("# proceed Process 1 Time {:.2f} # Customer {}'s product use plastic {:2f}g".format(self.env.now, customer_name, needed_plastic))
        yield self.env.process(use_material.get_plastic(customer_name, needed_plastic))
        yield self.env.timeout(print_time_FDM1)
        print("# finish Process 1 Time {:.2f} # Customer {}'s product is finished printing".format(self.env.now, customer_name))


class FDMPrinter_2(Printer):
    """    
    A class modeling the second FDM (Fused Deposition Modeling) printer.

    Attributes:
        resource (simpy.Resource): A SimPy Resource object representing FDMPrinter_2 (capacity=1).
    """
    def __init__(self, env):
        super().__init__(env)
        self.resource=simpy.Resource(env,capacity=1)
        
    def print(self, customer_name):
        """
        A process method that carries out a 3D printing job for a customer.

        1. Determines the required amount of plastic (needed_plastic) using a triangular distribution 
           (min=1g, mode=2g, max=3g).
        2. Determines the printing time (print_time_FDM2) using a triangular distribution 
           (min=8 minutes, mode=14 minutes, max=20 minutes).
        3. Prints a message including the current simulation time (env.now), customer name, and plastic usage.
        4. Calls the use_material.get_plastic process to obtain the required plastic amount.
        5. Waits for the specified print_time, then prints a completion message.

        Args:
            customer_name (str): The identifier for customer.

        Yields:
            simpy.Event: Sequentially waits for use_material.get_plastic and env.timeout events, 
            then signals that printing is complete.
        """
        needed_plastic = np.random.triangular(1, 2, 3)
        print_time_FDM2=np.random.triangular(8,14,20)
        print("# proceed Process 1 Time {:.2f} # Customer {}'s product use plastic {:2f}".format(self.env.now, customer_name, needed_plastic))
        yield self.env.process(use_material.get_plastic(customer_name, needed_plastic))
        yield self.env.timeout(print_time_FDM2)
        print("# finish Process 1 Time {:.2f} # Customer {}'s product is finished printing".format(self.env.now, customer_name))

class SLAPrinter_1(Printer):
    """
    A class modeling the first SLA (Stereolithography) printer.

    Attributes:
        env (simpy.Environment): The SimPy simulation environment.
        resource (simpy.Resource): A SimPy Resource object representing this printer (capacity=1).
    """ 
    def __init__(self, env):
        super().__init__(env)
        self.resource=simpy.Resource(env,capacity=1)
        
    def print(self, customer_name):
        """
        A process method that carries out an SLA printing job for a customer.

        1. Determines the required amount of resin (needed_resin) using a triangular distribution 
           (min=1ml, mode=2ml, max=3ml).
        2. Determines the printing time (print_time_SLA1) using a triangular distribution 
           (min=8 minutes, mode=10 minutes, max=20 minutes).
        3. Prints a message including the current simulation time (env.now), customer name, and resin usage.
        4. Calls the use_material.get_resin process to obtain the required resin amount.
        5. Waits for the specified print_time, then prints a completion message.

        Args:
            customer_name (str): The identifier for customer.

        Yields:
            simpy.Event: Sequentially waits for use_material.get_resin and env.timeout events,
                         then signals that printing is complete.
        """
        needed_resin = np.random.triangular(1,2,3)
        print_time_SLA1=np.random.triangular(8,10,20)
        print("# proceed Process 1 Time {:.2f} # Customer {}'s product use resin {:2f}ml".format(self.env.now, customer_name, needed_resin))
        yield self.env.process(use_material.get_resin(customer_name, needed_resin))
        yield self.env.timeout(print_time_SLA1)
        print("# finish Process 1 Time {:.2f} # Customer {}'s product is finished printing".format(self.env.now, customer_name))


class SLAPrinter_2(Printer):   
    def __init__(self, env):
        super().__init__(env)
        self.resource=simpy.Resource(env,capacity=1)
        
    def print(self, customer_name):
        """
        A process method that carries out an SLA printing job for a customer.

        1. Determines the required amount of resin (needed_resin) using a triangular distribution 
           (min=1ml, mode=2ml, max=3ml).
        2. Determines the printing time (print_time_SLA2) using a triangular distribution 
           (min=8 minutes, mode=15 minutes, max=20 minutes).
        3. Prints a message including the current simulation time (env.now), customer name, and resin usage.
        4. Calls the use_material.get_resin process to obtain the required resin amount.
        5. Waits for the specified print_time, then prints a completion message.

        Args:
            customer_name (str): The identifier for customer.

        Yields:
            simpy.Event: Sequentially waits for use_material.get_resin and env.timeout events,
                         then signals that printing is complete.
        """
        needed_resin = np.random.triangular(1,2,3)
        print_time_SLA2=np.random.triangular(8,15,20)
        print("# proceed Process 1 Time {:.2f} # Customer {}'s product use resin {:2f}ml".format(self.env.now, customer_name, needed_resin))
        yield self.env.process(use_material.get_resin(customer_name, needed_resin))
        yield self.env.timeout(print_time_SLA2)
        print("# finish Process 1 Time {:.2f} # Customer {}'s product is finished printing".format(self.env.now, customer_name))

#------------------------------------------------

class MaterialStock:
    """
    A class for managing material stocks.

    This class handles plastic and resin containers, providing the requested amounts to customers,
    or initiating a refill process if the requested amount exceeds current stock.
    """
    def __init__(self, env):
        self.env = env

    def get_plastic(self,customer_name, customer_needed_amount):
        """
        A process method that withdraws the requested amount of plastic from the container.

        1. If the plastic_container has at least customer_needed_amount, it withdraws immediately.
        2. If not enough stock is available, it prints a shortage message and calls refill_plastic.
        3. After refilling is complete, it withdraws the requested amount of plastic.

        Args:
            customer_name (str): The name or ID of the customer requesting the plastic.
            customer_needed_amount (float): The amount of plastic (in grams) needed by the customer.

        Yields:
            simpy.Event:
                - `plastic_container.get(customer_needed_amount)`: waits for plastic withdrawal.
                - `env.process(self.refill_plastic())`: waits for the refill process if stock is insufficient.
        """
        if plastic_container.level >= customer_needed_amount:
            yield plastic_container.get(customer_needed_amount)
        else:
            print("## Lack plastic to make Customer {}'s product ##".format(customer_name))
            yield self.env.process(self.refill_plastic())
            yield plastic_container.get(customer_needed_amount)

    def refill_plastic(self):
        """
        A process method that refills the plastic_container to its full capacity.

        1. Calculates refill_amount as (capacity - current level).
        2. Waits for the estimated refill time (refill_amount * 0.1), then puts refill_amount into the container.

        Yields:
            simpy.Event:
                - `env.timeout(refill_amount * 0.1)`: waits for the refill duration.
                - `plastic_container.put(refill_amount)`: waits for the refill action to complete.
        """
        refill_amount=plastic_container.capacity-plastic_container.level
        print("## Refill by{:.2f}, Estimate time{:.2f} ##".format(refill_amount,refill_amount*0.1))
        yield self.env.timeout(refill_amount*0.1)
        yield plastic_container.put(refill_amount)

    def get_resin(self,customer_name, customer_needed_amount):
        """
        A process method that withdraws the requested amount of resin from the container.

        1. If the resin_container has at least customer_needed_amount, it withdraws immediately.
        2. If not enough stock is available, it prints a shortage message and calls refill_resin.
        3. After refilling is complete, it withdraws the requested amount of resin.

        Args:
            customer_name (str): The name or ID of the customer requesting the resin.
            customer_needed_amount (float): The amount of resin (in milliliters) needed by the customer.

        Yields:
            simpy.Event:
                - `resin_container.get(customer_needed_amount)`: waits for resin withdrawal.
                - `env.process(self.refill_resin())`: waits for the refill process if stock is insufficient.
        """
        if resin_container.level >= customer_needed_amount:
            yield resin_container.get(customer_needed_amount)
        else:
            print("## Lack plastic to make Customer {}'s product ##".format(customer_name))
            yield self.env.process(self.refill_resin())
            yield resin_container.get(customer_needed_amount)

    def refill_resin(self):
        """
        A process method that refills the resin_container to its full capacity.

        1. Calculates refill_amount as (capacity - current level).
        2. Waits for the estimated refill time (refill_amount * 0.1), then puts refill_amount into the container.

        Yields:
            simpy.Event:
                - `env.timeout(refill_amount * 0.1)`: waits for the refill duration.
                - `resin_container.put(refill_amount)`: waits for the refill action to complete.
        """
        refill_amount=resin_container.capacity-resin_container.level
        print("## Refill by{:.2f}, Estimate time{:.2f} ##".format(refill_amount,refill_amount*0.1))
        yield self.env.timeout(refill_amount*0.1)
        yield resin_container.put(refill_amount)

#------------------------------------------

class QualityControl:
    def __init__(self, env):
        self.env = env

    def inspect(self, customer_name, printer_type):
        """
        A process method that performs quality control on a customer's printed product.

        1. Requests the qc_resource to begin inspection.
        2. Prints a message indicating that the product has entered quality control, 
           including the current simulation time and customer name.
        3. Samples an inspection time from a uniform distribution between 1 and 3 time units.
        4. Waits for the inspection_time to simulate the QC process.
        5. With a 5% chance, the product fails QC:
           a. Prints a failure message with the current time and customer name.
           b. Re-enters the printing process (printing_process) using the same printer_type.
        6. Otherwise, the product passes QC:
           a. Prints a pass message with the current time and customer name.
           b. Proceeds to the packaging process (packaging_team.package).
        
        Args:
            customer_name (str): The name or ID of the customer whose product is being inspected.
            printer_type (int): The type of printer used (0 for FDM, 1 for SLA), 
                                used to determine reprint behavior on failure.

        Yields:
            simpy.events.AnyOf / simpy.Event:
                - `qc_resource.request()`: waits for the quality control resource to become available.
                - `env.timeout(inspection_time)`: simulates the inspection duration.
                - On failure: `env.process(printing_process(...))` waits for the reprint process to complete.
                - On success: `env.process(packaging_team.package(...))` waits for the packaging process to complete.
        """
        with qc_resource.request() as req:
            yield req
            print("# enter process2 Time {:.2f} # customer's product {} enters Quality Control"
                  .format(self.env.now, customer_name))
            inspection_time = np.random.uniform(1, 3)
            yield self.env.timeout(inspection_time)

            if np.random.rand() < 0.05:
                print("# fail Process 2 reenter process1 # Time {:.2f} # customer's product {} failed QC"
                      .format(self.env.now, customer_name))
                # On QC failure, re-enter the printing process with the same printer_type
                yield self.env.process(printing_process(self.env, customer_name, printer_type))
            else:
                print("# finish Process 2 Time {:.2f} # customer's product {} passed QC"
                      .format(self.env.now, customer_name))
                # On success, proceed to packaging
                yield self.env.process(packaging_team.package(customer_name))


# -------------------------------------------------
class PackagingStation:
    def __init__(self, env):
        self.env = env

    def package(self, customer_name):
        """
        A process method that packages a customer's product.

        1. Requests the packaging_resource to begin packaging.
        2. Prints a message indicating that the product has started packaging, 
           including the current simulation time and customer name.
        3. Samples a packaging time from a triangular distribution with parameters (2, 3, 5).
        4. Waits for the pack_time to simulate the packaging process.
        5. Prints a completion message with the current time and customer name.

        Args:
            customer_name (str): The name or ID of the customer whose product is being packaged.

        Yields:
            simpy.events.AnyOf / simpy.Event:
                - `packaging_resource.request()`: waits for the packaging station to become available.
                - `env.timeout(pack_time)`: simulates the duration of the packaging process.
        """
        with packaging_resource.request() as req:
            yield req
            pack_time = np.random.triangular(2, 3, 5)
            print("# Enter process 3 Time {:.2f} # customer's product {} starts packaging"
                  .format(self.env.now, customer_name))
            yield self.env.timeout(pack_time)
            print("# finish process 3 Time {:.2f} # customer's product {} completed packaging"
                  .format(self.env.now, customer_name))


# ---------------------------------------------------------------------------------------

env=simpy.Environment()
reception_desk=simpy.Resource(env, capacity=1)
blueprint_station=simpy.Resource(env, capacity=2)



fdm_printer_1=FDMPrinter_1(env)
fdm_printer_2=FDMPrinter_2(env)
sla_printer_1=SLAPrinter_1(env)
sla_printer_2=SLAPrinter_2(env)

use_material=MaterialStock(env)
plastic_container=simpy.Container(env,init=20,capacity=1000)
resin_container=simpy.Container(env,init=20,capacity=1000)

qc_resource = simpy.Resource(env, capacity=2)
qc_team=QualityControl(env)

packaging_resource = simpy.Resource(env, capacity=2)
packaging_team=PackagingStation(env)



env.process(generate_customer(env, TOTAL_CUSTOMERS=20, INTERVAL=15))
env.run()